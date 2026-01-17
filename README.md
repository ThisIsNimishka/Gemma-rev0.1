# VCAP - Visual Computing Automation Platform

**Version: VCAP-rev0.1 (ISV Automation Release)**

VCAP (Visual Computing Automation Platform) is a **computer vision-based automation framework for ISV applications and Copilot/AI feature testing**. It uses a distributed Client-Server architecture where a Controller machine orchestrates multiple Systems Under Test (SUTs) running productivity and creative workloads.

---

## 🚀 Key Features

| Feature | Description |
|---------|-------------|
| **Multi-SUT Control** | Manage multiple test machines from a single controller with independent automation threads |
| **Vision-Driven Automation** | Uses Vision Language Models (OmniParser, Gemini, Qwen) for robust UI element detection without DOM access |
| **ISV Workload Support** | Designed for Adobe Creative Cloud, Microsoft Office, Autodesk, and other complex ISV applications |
| **Copilot & AI Testing** | Features for evaluating AI response latency, accuracy, and NPU utilization (Planned) |
| **Campaign Mode** | Queue multiple test suites with configurable iteration counts and delays |
| **Step-Based Automation** | YAML-defined automation workflows with "Find-and-Act" patterns |
| **State Machine Engine** | Handle complex application flows, popups, and non-deterministic states |
| **Live Preview** | Real-time SUT monitoring via low-latency screenshot streaming |
| **Robust Process Management** | Reliable launching, foreground enforcement, and crash detection for ISV apps |

---

## 📂 Project Structure

```
VCAP/
├── gui_app_multi_sut.py      # Main Controller GUI (Tkinter)
├── workflow_builder.py       # Visual workflow/config builder tool
├── modules/                  # Core automation logic
│   ├── network.py            # HTTP client for SUT communication
│   ├── screenshot.py         # Screenshot capture and caching
│   ├── game_launcher.py      # App/Process launcher (Generic)
│   ├── simple_automation.py  # Step-based automation engine
│   ├── decision_engine.py    # State machine automation engine
│   ├── omniparser_client.py  # OmniParser vision model client
│   └── annotator.py          # Screenshot annotation utilities
│
├── sut_service_installer/    # SUT Agent files
│   ├── gemma_service_0.2.py  # ⭐ Latest SUT agent with optimizations
│   └── requirements.txt      # SUT dependencies
│
├── config/                   # Configuration files
│   ├── workloads/            # App-specific automation YAMLs
│   │   ├── photoshop_export.yaml
│   │   ├── excel_pivot_tables.yaml
│   │   └── ...
│   └── campaigns/            # Campaign definitions
│
└── omniparser_queue_service.py  # Batch OmniParser processing
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.10+
- Windows 10/11 (SUT machines)
- [OmniParser](https://github.com/microsoft/OmniParser) running on localhost:9000

### 1. Controller Machine Setup

```bash
# Clone repository
git clone https://github.com/YourOrg/VCAP.git
cd VCAP

# Install dependencies
pip install tkinter pillow pyyaml requests

# Run the controller
python gui_app_multi_sut.py
```

### 2. SUT (Test Machine) Setup

```bash
# Copy sut_service_installer folder to test machine
cd sut_service_installer

# Install dependencies
pip install -r requirements.txt

# Run as Administrator (required for input simulation)
python gemma_service_0.2.py
```

---

## 🧪 Quick Start (ISV Automation)

1. **Start OmniParser** on localhost:9000
2. **Start Agent** on your test machine (SUT)
3. **Launch Controller**: `python gui_app_multi_sut.py`
4. **Add SUT**: Enter IP and port of your test machine
5. **Select Workload**: Choose an automation YAML from `config/workloads/`
6. **Start Test**: Click "Start" to execute the automation workflow

---

## 📝 Configuration Files

### Workload Config Example (`config/workloads/photoshop.yaml`)

```yaml
metadata:
  app_name: Adobe Photoshop 2024
  path: C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe
  process_id: Photoshop
  startup_wait: 30

steps:
  1:
    description: CLICK FILE MENU
    find:
      type: text
      text: File
    action:
      type: click
      button: left
    timeout: 10
  
  2:
    description: SELECT NEW
    find:
      type: text
      text: New...
    action:
      type: click
  
  3:
    description: CLICK CREATE
    find:
      type: text
      text: Create
    action:
      type: click
      expected_delay: 5
```

---

## 📋 Changelog (VCAP Transformation)

| File | Change | Reason |
|------|--------|--------|
| `gui_app_multi_sut.py` | Branding | Updated UI labels to VCAP |
| `README.md` | **Major Update** | Rebranded to VCAP, focused on ISV/Copilot use cases |
| `config/workloads/` | **New** | Created folder for ISV app configurations |

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Access Denied" launching apps | Run agent as **Administrator** |
| Window not focusing | Ensure `startup_wait` is sufficient for heavy ISV apps |
| Vision detection failing | Verify OmniParser is running and model is loaded |

---

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.

---
**Built for ...... Nothing 🏁**
