#!/usr/bin/env python3
"""Merge ODS quantities with enriched Excel metadata."""

from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from openpyxl import load_workbook
import json
from collections import defaultdict

def main():
    # STEP 1: Read ODS - get component names and quantities (merge duplicates)
    doc = load('COMPONENTS_DATA.ods')
    sheets = doc.spreadsheet.getElementsByType(Table)
    sheet = sheets[0]

    ods_components = defaultdict(lambda: {"qty": 0, "descriptions": []})

    for row in sheet.getElementsByType(TableRow)[1:]:
        cells = row.getElementsByType(TableCell)
        row_data = []
        for cell in cells:
            text_content = ''
            for p in cell.getElementsByType(P):
                text_content += str(p)
            repeat = cell.getAttribute('numbercolumnsrepeated')
            if repeat:
                for _ in range(min(int(repeat), 10)):
                    row_data.append(text_content.strip())
            else:
                row_data.append(text_content.strip())
        
        if len(row_data) >= 4 and row_data[0] and row_data[2]:
            description = row_data[1].strip() if row_data[1] else ""
            component = row_data[2].strip().upper()
            try:
                qty = int(row_data[3]) if row_data[3] else 1
            except:
                qty = 1
            
            ods_components[component]["qty"] += qty
            if description and description not in ods_components[component]["descriptions"]:
                ods_components[component]["descriptions"].append(description)

    print(f"ODS: {len(ods_components)} unique components")

    # STEP 2: Read enriched Excel - get metadata
    wb = load_workbook('COMPONENTS_DATA_ENRICHED.xlsx')
    excel_sheet = wb.active

    enriched_data = {}
    for row in excel_sheet.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        original_name = (row[1] or "").strip().upper()
        enriched_data[original_name] = {
            "mpn": row[2] if row[2] and row[2] != "N/A" else None,
            "common_name": row[3] if row[3] else None,
            "description": row[4] if row[4] else None,
            "package": row[6] if row[6] else None,
            "specs": row[7] if row[7] else None,
            "category": row[8] if row[8] else "Electronic Component",
            "datasheet": row[9] if row[9] else None
        }

    print(f"Enriched Excel: {len(enriched_data)} rows")

    # STEP 3: Merge - ODS quantities + enriched metadata
    final_components = []
    matched = 0
    unmatched = 0

    for i, (component, ods_data) in enumerate(sorted(ods_components.items()), start=1):
        enriched = enriched_data.get(component)
        
        if enriched:
            matched += 1
            comp = {
                "id": f"comp_{i:03d}",
                "original_name": component,
                "name": enriched["common_name"] or component.title(),
                "mpn": enriched["mpn"],
                "description": enriched["description"],
                "quantity": ods_data["qty"],
                "package": enriched["package"],
                "specifications": enriched["specs"],
                "category": enriched["category"],
                "datasheet_url": enriched["datasheet"],
                "status": "available"
            }
        else:
            unmatched += 1
            desc = ods_data["descriptions"][0] if ods_data["descriptions"] else component
            comp = {
                "id": f"comp_{i:03d}",
                "original_name": component,
                "name": component.title(),
                "mpn": None,
                "description": desc,
                "quantity": ods_data["qty"],
                "package": None,
                "specifications": None,
                "category": "Electronic Component",
                "datasheet_url": None,
                "status": "available"
            }
        
        final_components.append(comp)

    print(f"Matched: {matched}, Unmatched: {unmatched}")

    # STEP 4: Add 8 cart items
    cart_items = [
        {"id": "comp_cart_01", "original_name": "SIPEED SLOGIC COMBO 8", "name": "Sipeed SLogic Combo 8 Logic Analyzer", "mpn": "SLogic Combo 8", "description": "The Daily Driver. 8-channel logic analyzer decodes UART, SPI, I2C, PWM.", "quantity": 1, "package": None, "specifications": "8 channels, USB interface", "category": "Tool / Measurement", "datasheet_url": None, "status": "ordered", "price_inr": 1559},
        {"id": "comp_cart_02", "original_name": "WEACT USB-CAN ANALYZER", "name": "WeAct USB-CAN Analyzer (CAN-FD)", "mpn": "USB-CAN Analyzer", "description": "Decodes CAN bus traffic for automotive projects.", "quantity": 1, "package": None, "specifications": "CAN-FD support, USB", "category": "Tool / Measurement", "datasheet_url": None, "status": "ordered", "price_inr": 1075},
        {"id": "comp_cart_03", "original_name": "SN65HVD230 CAN BOARD", "name": "SN65HVD230 CAN Transceiver Board", "mpn": "SN65HVD230 (TI)", "description": "Connects STM32 to CAN Bus.", "quantity": 2, "package": "Module", "specifications": "3.3V, CAN 2.0", "category": "Bus Transceiver", "datasheet_url": "https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf", "status": "ordered", "price_inr": 418},
        {"id": "comp_cart_04", "original_name": "MCP2003-E/P LIN", "name": "MCP2003-E/P LIN Transceiver", "mpn": "MCP2003-E/P (Microchip)", "description": "Connects STM32 to LIN Bus.", "quantity": 2, "package": "DIP-8", "specifications": "LIN 2.x compatible", "category": "Bus Transceiver", "datasheet_url": "https://ww1.microchip.com/downloads/en/DeviceDoc/20002230G.pdf", "status": "ordered", "price_inr": 152},
        {"id": "comp_cart_05", "original_name": "ENC28J60", "name": "ENC28J60 Ethernet Module", "mpn": "ENC28J60 (Microchip)", "description": "SPI-based Ethernet controller for TCP/IP.", "quantity": 1, "package": "Module", "specifications": "10Base-T, SPI", "category": "Ethernet Module", "datasheet_url": "https://ww1.microchip.com/downloads/en/DeviceDoc/39662e.pdf", "status": "ordered", "price_inr": 299},
        {"id": "comp_cart_06", "original_name": "TXS0108E", "name": "TXS0108E Logic Level Converter", "mpn": "TXS0108E (TI)", "description": "5V <-> 3.3V bidirectional level shifting.", "quantity": 1, "package": "Module", "specifications": "8-ch bidirectional", "category": "Logic Level Converter", "datasheet_url": "https://www.ti.com/lit/ds/symlink/txs0108e.pdf", "status": "ordered", "price_inr": 48},
        {"id": "comp_cart_07", "original_name": "INA219", "name": "INA219 Current Sensor", "mpn": "INA219 (TI)", "description": "I2C current/voltage sensor.", "quantity": 1, "package": "Module", "specifications": "I2C, 0-26V, 3.2A max", "category": "Sensor Module", "datasheet_url": "https://www.ti.com/lit/ds/symlink/ina219.pdf", "status": "ordered", "price_inr": 200},
        {"id": "comp_cart_08", "original_name": "USB MICROSCOPE 1000X", "name": "USB Microscope 1000X", "mpn": None, "description": "For inspecting solder joints and SMD components.", "quantity": 1, "package": "USB Device", "specifications": "1000X magnification", "category": "Tool / Measurement", "datasheet_url": None, "status": "ordered", "price_inr": None}
    ]
    final_components.extend(cart_items)

    # STEP 5: Save
    inventory = {
        "metadata": {
            "version": "2.2",
            "last_updated": "2026-01-05",
            "owner": "Nani",
            "notes": "ODS quantities + enriched metadata + 8 ordered items"
        },
        "components": final_components,
        "summary": {
            "total_unique_components": len(final_components),
            "total_quantity": sum(c["quantity"] for c in final_components),
            "matched_with_enriched_data": matched,
            "ods_only": unmatched,
            "ordered_items": 8
        }
    }

    with open('embedded_tracker/data/hardware_inventory.json', 'w') as f:
        json.dump(inventory, f, indent=4)

    print(f"Saved {len(final_components)} components")
    print(f"Total quantity: {inventory['summary']['total_quantity']}")

if __name__ == "__main__":
    main()
