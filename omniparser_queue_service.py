"""
Omniparser Queue Service - Middleware for handling multiple SUT requests
Queues requests and forwards them sequentially to a single Omniparser server.
Prevents request denial when multiple SUTs send requests simultaneously.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Dummy classes for type hinting/runtime safety if imported but not run
    class BaseModel: pass
    class FastAPI: 
        def __init__(self, **kwargs): pass
        def get(self, path): return lambda x: x
        def post(self, path): return lambda x: x
    class HTTPException(Exception): pass
    Request = Any
    JSONResponse = Any
    uvicorn = None

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("omniparser_queue_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OMNIPARSER_SERVER_URL = "http://localhost:8000"  # Target Omniparser server
REQUEST_TIMEOUT = 120  # Timeout for Omniparser requests in seconds
MAX_QUEUE_SIZE = 100  # Maximum number of requests in queue

# Request model
class ParseRequest(BaseModel):
    base64_image: str
    box_threshold: float = 0.05
    iou_threshold: float = 0.1
    use_paddleocr: bool = True

@dataclass
class QueuedRequest:
    """Represents a queued request with its metadata."""
    request_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    response_future: asyncio.Future = field(default_factory=asyncio.Future)

class OmniparserQueueManager:
    """Manages the request queue and forwards requests to Omniparser server."""

    def __init__(self, target_url: str, timeout: int = 120):
        self.target_url = target_url
        self.timeout = timeout
        self.request_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self.worker_task: Optional[asyncio.Task] = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "current_queue_size": 0,
            "worker_running": False
        }
        self.session = requests.Session()
        logger.info(f"OmniparserQueueManager initialized with target: {target_url}")

    async def start_worker(self):
        """Start the background worker that processes queued requests."""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("Queue worker started")

    async def stop_worker(self):
        """Stop the background worker."""
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Queue worker stopped")

    async def _worker(self):
        """Background worker that processes requests from the queue one at a time."""
        logger.info("Worker thread started, processing requests sequentially")
        self.stats["worker_running"] = True

        while True:
            try:
                # Get next request from queue
                queued_request: QueuedRequest = await self.request_queue.get()
                self.stats["current_queue_size"] = self.request_queue.qsize()

                logger.info(f"Processing request {queued_request.request_id} (Queue size: {self.request_queue.qsize()})")

                # Process the request
                try:
                    response_data = await self._forward_to_omniparser(queued_request)
                    queued_request.response_future.set_result(response_data)
                    self.stats["successful_requests"] += 1
                    logger.info(f"Request {queued_request.request_id} completed successfully")
                except Exception as e:
                    logger.error(f"Request {queued_request.request_id} failed: {str(e)}")
                    queued_request.response_future.set_exception(e)
                    self.stats["failed_requests"] += 1

                # Mark task as done
                self.request_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Worker cancelled, shutting down")
                self.stats["worker_running"] = False
                break
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)  # Avoid tight loop on errors

    async def _forward_to_omniparser(self, queued_request: QueuedRequest) -> Dict[str, Any]:
        """
        Forward a request to the Omniparser server (synchronous call in thread pool).

        Args:
            queued_request: The queued request to process

        Returns:
            Response data from Omniparser

        Raises:
            HTTPException: If the request fails
        """
        start_time = time.time()

        try:
            # Run synchronous request in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.post(
                    f"{self.target_url}/parse/",
                    json=queued_request.payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
            )

            # Check response status
            if response.status_code != 200:
                logger.error(f"Omniparser returned status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Omniparser server error: {response.text}"
                )

            response_data = response.json()
            processing_time = time.time() - start_time

            logger.info(f"Omniparser processing completed in {processing_time:.2f}s")

            return response_data

        except requests.Timeout:
            logger.error(f"Request {queued_request.request_id} timed out after {self.timeout}s")
            raise HTTPException(status_code=504, detail="Omniparser request timed out")
        except requests.RequestException as e:
            logger.error(f"Request {queued_request.request_id} failed: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Failed to connect to Omniparser: {str(e)}")

    async def enqueue_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a request to the queue and wait for its result.

        Args:
            payload: Request payload to forward to Omniparser

        Returns:
            Response from Omniparser

        Raises:
            HTTPException: If queue is full or request fails
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]

        # Check queue size
        current_size = self.request_queue.qsize()
        if current_size >= MAX_QUEUE_SIZE:
            logger.warning(f"Queue full ({current_size}/{MAX_QUEUE_SIZE}), rejecting request")
            raise HTTPException(status_code=503, detail="Queue is full, please retry later")

        # Create queued request
        queued_request = QueuedRequest(
            request_id=request_id,
            payload=payload
        )

        self.stats["total_requests"] += 1

        # Add to queue
        await self.request_queue.put(queued_request)
        queue_position = self.request_queue.qsize()
        logger.info(f"Request {request_id} queued at position {queue_position}")

        self.stats["current_queue_size"] = queue_position

        # Wait for result
        try:
            result = await queued_request.response_future
            return result
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get current queue statistics."""
        return {
            **self.stats,
            "current_queue_size": self.request_queue.qsize()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check health of the Omniparser server."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(f"{self.target_url}/probe", timeout=5)
            )
            response.raise_for_status()
            return {
                "status": "healthy",
                "omniparser_server": self.target_url,
                "omniparser_response": response.json()
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "omniparser_server": self.target_url,
                "error": str(e)
            }

# Global queue manager instance
queue_manager = OmniparserQueueManager(
    target_url=OMNIPARSER_SERVER_URL,
    timeout=REQUEST_TIMEOUT
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Omniparser Queue Service")
    logger.info(f"Target Omniparser server: {OMNIPARSER_SERVER_URL}")
    logger.info(f"Request timeout: {REQUEST_TIMEOUT}s")
    logger.info(f"Max queue size: {MAX_QUEUE_SIZE}")
    await queue_manager.start_worker()

    yield

    # Shutdown
    logger.info("Shutting down Omniparser Queue Service")
    await queue_manager.stop_worker()

# FastAPI app with lifespan
app = FastAPI(
    title="Omniparser Queue Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/probe")
async def probe():
    """
    Health check endpoint - compatible with OmniparserClient.
    Returns queue service health and Omniparser server health.
    """
    health_status = await queue_manager.health_check()
    stats = queue_manager.get_stats()

    return {
        "service": "omniparser_queue_service",
        "version": "1.0.0",
        "queue_service_status": "running",
        "omniparser_status": health_status,
        "stats": stats
    }

@app.post("/parse/")
async def parse_image(request: ParseRequest):
    """
    Parse image endpoint - queues request and forwards to Omniparser.
    Compatible with OmniparserClient API format.

    Args:
        request: Parse request with base64_image and parameters

    Returns:
        Omniparser response with parsed_content_list and som_image_base64
    """
    try:
        # Convert request to dict
        payload = request.dict()

        # Enqueue and wait for result
        logger.info(f"Received parse request (image size: {len(payload['base64_image'])} bytes)")
        result = await queue_manager.enqueue_request(payload)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get queue statistics and performance metrics."""
    return queue_manager.get_stats()

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Omniparser Queue Service",
        "version": "1.0.0",
        "target_server": OMNIPARSER_SERVER_URL,
        "endpoints": {
            "parse": "/parse/",
            "health": "/probe",
            "stats": "/stats"
        }
    }

def main():
    """Run the queue service."""
    import argparse

    parser = argparse.ArgumentParser(description="Omniparser Queue Service")
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Port to run the service on (default: 9000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--omniparser-url",
        type=str,
        default=OMNIPARSER_SERVER_URL,
        help=f"Omniparser server URL (default: {OMNIPARSER_SERVER_URL})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=REQUEST_TIMEOUT,
        help=f"Request timeout in seconds (default: {REQUEST_TIMEOUT})"
    )

    args = parser.parse_args()

    # Update queue manager configuration
    queue_manager.target_url = args.omniparser_url
    queue_manager.timeout = args.timeout

    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Forwarding to Omniparser at {args.omniparser_url}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
