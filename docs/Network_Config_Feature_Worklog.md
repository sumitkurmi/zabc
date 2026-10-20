# Network Configuration Feature: Implementation & Testing Work Log

**Project:** AI-Assisted Network Complaint Portal  
**Feature:** OS-specific hostel network configuration downloads  
**Document date:** 20 October 2026  
**Implementation environment:** Ubuntu Linux, VS Code, React/Vite frontend, FastAPI backend

---

## 1. Feature Objective

Add a network-configuration entry point to the existing Network Assistant. Students can open **Configure Proxy & IPv4**, choose their operating system, and download the matching helper script.

- **Linux / Ubuntu:** `configure_hostel_network.py`
- **Windows:** `configure_hostel_network.ps1`

The OS selector is embedded in the existing configuration panel so the original chatbot layout and core chat features remain in place.

## 2. High-Level Architecture

```text
Student opens Network Assistant
              |
              v
Clicks "Configure Proxy & IPv4"
              |
              v
Chooses operating system
       /                    \
      v                      v
Linux / Ubuntu             Windows
      |                      |
      v                      v
GET /api/network-config/download?os_name=linux
                         GET /api/network-config/download?os_name=windows
      |                      |
      v                      v
FastAPI selects the matching script from /scripts
              |
              v
Browser downloads the selected file
              |
              v
User reviews the script instructions
```

The current Windows script only previews settings. It does not apply network changes.

## 3. Files Involved and Responsibilities

### 3.1 `scripts/configure_hostel_network.py`

**Purpose:** Existing Linux/Ubuntu network configuration helper for the C Block room allocation.

**Behavior:**
1. Checks that the script is running on Linux and that `nmcli` is available.
2. Prompts for the hostel and accepts the configured C Block aliases.
3. Prompts for a room number and checks it against the generated room mapping.
4. Displays the proposed IPv4 address, prefix, subnet mask, gateway, DNS, and proxy endpoints.
5. Finds active NetworkManager connections for Wi-Fi and Ethernet.
6. If multiple active connections are found, asks the user to choose one.
7. Requires the user to type `APPLY` before attempting to modify IPv4 settings.
8. Saves selected previous NetworkManager values to a local backup file and attempts rollback if applying IPv4 settings fails.
9. Attempts to set GNOME HTTP/HTTPS proxy settings with `gsettings`, if available.

**Important limitations:** The backup and rollback are best-effort and do not guarantee recovery. The script can disconnect the device if the IP details or campus policy are incorrect. Proxy handling currently uses the first listed proxy endpoint for GNOME HTTP/HTTPS settings; the source PDF alone does not clarify the intended relationship between both endpoints.

### 3.2 `scripts/configure_hostel_network.ps1`

**Purpose:** Windows PowerShell preview helper.

**Current behavior:**
1. Prompts for a room number.
2. Rejects values outside the coded C Block room ranges.
3. Calculates a proposed IPv4 address.
4. Detects active Windows network adapters and displays their details.
5. Displays the proposed IP, subnet mask, `/23` prefix, gateway, DNS servers, and proxy endpoints.
6. Clearly reports that it is preview-only.

**Not implemented:** It does not change Windows IPv4, DNS, or proxy settings. It has not yet been executed in Windows PowerShell, so Windows runtime behavior remains unverified.

### 3.3 `backend/app/routers/network_config.py`

**Purpose:** OS-specific script download endpoint.

The router maps supported query values to the appropriate script:

| `os_name` value | Script returned | Download filename |
|---|---|---|
| `linux` | `scripts/configure_hostel_network.py` | `configure_hostel_network.py` |
| `ubuntu` | `scripts/configure_hostel_network.py` | `configure_hostel_network.py` |
| `windows` | `scripts/configure_hostel_network.ps1` | `configure_hostel_network.ps1` |

**Endpoint:** `GET /api/network-config/download`

The router checks that the selected script exists before returning it. Unsupported OS values produce HTTP 400; a missing script produces HTTP 500.

### 3.4 `frontend/src/components/chat/ChatPanel.tsx`

**Purpose:** UI integration inside the existing chatbot panel.

**Changes:**
1. Added state to track the selected operating system (`linux` or `windows`).
2. Added Windows and Linux / Ubuntu selection controls inside the existing **Configure Proxy & IPv4** panel.
3. Changed the download request to include the selected `os_name`.
4. Changed the downloaded filename and button label to match the selected OS.
5. Added handling for failed downloads and user-facing error messages.
6. Added OS-specific run instructions and a safety warning.

The existing suggestion chips, message list, message input, chat limit notice, and AI complaint-summary action were retained.

## 4. API Usage

**Route:** `GET /api/network-config/download`

```text
GET /api/network-config/download?os_name=linux
GET /api/network-config/download?os_name=ubuntu
GET /api/network-config/download?os_name=windows
```

The frontend uses a relative `/api/...` URL so the request follows the app's existing frontend/backend routing setup.

## 5. Network Settings Represented in the Scripts

The following values were transcribed from the supplied C Block IP allocation material. They have not been independently confirmed as current with the campus network administrator.

| Setting | Value |
|---|---|
| Gateway | `172.31.68.1` |
| Subnet mask | `255.255.254.0` |
| Prefix length | `/23` |
| DNS servers | `172.31.100.6`, `172.31.100.7`, `172.31.100.8` |
| Proxy endpoints listed in the PDF | `172.31.100.27:3128`, `172.31.102.29:3128` |

The PDF does not, by itself, establish whether the two proxy endpoints are primary/backup or protocol-specific. Proxy credentials must not be embedded in downloaded scripts.

### 5.1 Sample Room/IP Calculation Checks

| Room | Calculated IP |
|---:|---|
| 101 | `172.31.68.60` |
| 204 | `172.31.68.91` |
| 727 | `172.31.68.254` |
| 728 | `172.31.69.0` |
| 801 | `172.31.69.1` |
| 1328 | `172.31.69.168` |

An earlier temporary Python test incorrectly calculated the same address for rooms 728 and 801. A separate corrected arithmetic check returned the distinct values shown above. The complete mapping must still be checked against the original allocation PDF before operational use.

## 6. Testing Performed

### 6.1 Backend and API

- Started FastAPI with Uvicorn at `127.0.0.1:8000`.
- Confirmed that the OpenAPI document returned HTTP 200.
- Confirmed that `/api/network-config/download` appeared in OpenAPI.
- Downloaded the Windows script using `curl` to `/tmp/configure_hostel_network.ps1`.
- Checked the beginning of the downloaded file and confirmed it contained the expected PowerShell script comments.

### 6.2 Frontend

- Ran the Vite frontend at `http://localhost:5174/`.
- Opened the Network Assistant.
- Opened the **Configure Proxy & IPv4** panel.
- Selected Windows and confirmed the Windows script downloaded.
- Selected Linux / Ubuntu and confirmed the Linux script download worked.
- Reported no new TypeScript errors after replacing `ChatPanel.tsx`.

## 7. Local Development Setup

### Frontend terminal

```bash
cd "$HOME/mini project/Semester_7_Project/frontend"
npm run dev
```

### Backend terminal

```bash
cd "$HOME/mini project/Semester_7_Project"
source .venv/bin/activate
PYTHONPATH=. python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Keep both terminals open while testing the application.

## 8. Safety and Operational Considerations

1. **Windows is preview-only:** Do not describe the current PowerShell script as applying network settings.
2. **Confirm the official mapping:** Verify all room/IP assignments against the original C Block allocation document.
3. **Confirm campus policy:** Ask the network administrator whether static IPv4 configuration is permitted and whether the gateway, DNS, and proxy values are current.
4. **Possible disconnection:** Applying an incorrect static IP can disconnect a laptop from the network.
5. **Rollback is not guaranteed:** The Linux script's backup and rollback are best-effort only.
6. **Keep secrets out:** Do not embed proxy credentials or commit `.env` files, tokens, or passwords.
7. **Test Windows separately:** Run the preview script on a Windows test machine before implementing any actual network modifications.

## 9. Current Status

### Completed

- Created the Windows PowerShell helper in preview-only form.
- Updated the FastAPI router to serve the correct script for Linux/Ubuntu or Windows.
- Added the OS selector and OS-specific download behavior to `ChatPanel.tsx`.
- Tested both downloads through the browser.
- Confirmed the API route was registered in OpenAPI.
