"""
find_bt_port.py — 列出所有 COM 埠並標示藍牙相關的（含裝置名稱查詢）
用法: python find_bt_port.py
"""
import re
import serial.tools.list_ports


def get_bt_friendly_names() -> dict[str, str]:
    """從 Windows 登錄檔讀取已配對藍牙裝置名稱，回傳 {MAC: name}。"""
    names: dict[str, str] = {}
    try:
        import winreg
        key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as root:
            i = 0
            while True:
                try:
                    mac_hex = winreg.EnumKey(root, i)   # e.g. "98d331905917"
                    with winreg.OpenKey(root, mac_hex) as dev:
                        try:
                            name, _ = winreg.QueryValueEx(dev, "Name")
                            if isinstance(name, (bytes, bytearray)):
                                name = name.rstrip(b"\x00").decode("utf-8", errors="ignore")
                            names[mac_hex.upper()] = name
                        except FileNotFoundError:
                            pass
                    i += 1
                except OSError:
                    break
    except Exception:
        pass
    return names


def mac_from_hwid(hwid: str) -> str | None:
    """從 HWID 字串中擷取 12 位十六進位 MAC，回傳大寫無分隔符的字串。"""
    m = re.search(r"([0-9A-Fa-f]{12})_C", hwid)   # HC-05/06 傳出格式
    if not m:
        m = re.search(r"([0-9A-Fa-f]{12})", hwid)
    return m.group(1).upper() if m else None


# ---- 主程式 --------------------------------------------------
bt_names = get_bt_friendly_names()

ports = list(serial.tools.list_ports.comports())

if not ports:
    print("找不到任何 COM 埠。請確認驅動程式已安裝。")
else:
    print(f"共找到 {len(ports)} 個 COM 埠：\n")
    print(f"{'埠號':<8} {'藍牙裝置名稱':<18} {'裝置描述':<38} HWID (節錄)")
    print("-" * 100)
    for p in sorted(ports, key=lambda x: int(x.device.replace("COM", ""))):
        desc = p.description or "(無描述)"
        hwid = p.hwid or ""
        is_bt = "BTHENUM" in hwid.upper()

        bt_label = ""
        if is_bt:
            mac = mac_from_hwid(hwid)
            if mac and mac in bt_names:
                bt_label = bt_names[mac]
            else:
                bt_label = "(未知裝置)"

        marker = "  ← 藍牙" if is_bt else ""
        hwid_short = hwid[:55] + "…" if len(hwid) > 55 else hwid
        print(f"{p.device:<8} {bt_label:<18} {desc:<38} {hwid_short}{marker}")

print()
print("提示：")
print("  - 藍牙欄顯示已配對裝置的名稱（例如 HC-06、FaceDoor）")
print("  - HC-05/HC-06 通常會有兩個 COM 埠，名稱相同，號碼較大的是「傳出」")
print("  - 將「傳出」埠號填入 config.SERIAL_PORT（或保持 AUTO 自動偵測）")
