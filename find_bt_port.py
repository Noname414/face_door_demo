"""
find_bt_port.py — 列出所有 COM 埠並標示藍牙相關的
用法: python find_bt_port.py
"""
import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())

if not ports:
    print("找不到任何 COM 埠。請確認驅動程式已安裝。")
else:
    print(f"共找到 {len(ports)} 個 COM 埠：\n")
    print(f"{'埠號':<10} {'裝置描述':<45} {'HWID'}")
    print("-" * 90)
    for p in sorted(ports, key=lambda x: int(x.device.replace("COM", ""))):
        desc = p.description or "(無描述)"
        hwid = p.hwid or ""
        marker = "  ← 可能是藍牙" if "bluetooth" in desc.lower() or "bluetooth" in hwid.lower() else ""
        print(f"{p.device:<10} {desc:<45} {hwid}{marker}")

print()
print("提示：")
print("  - HC-05/HC-06 通常顯示為「標準序列透過藍牙連結」")
print("  - 會出現兩個 COM 埠，號碼較大的是「傳出」，填入 config.SERIAL_PORT")
