#!/usr/bin/env python3
"""Fix broken resource URLs with verified replacements"""

from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import Resource
from sqlmodel import select

# URL corrections: ID -> new_url
CORRECTIONS = {
    # MCUboot - use official mcuboot.com
    28: "https://mcuboot.com/documentation/",
    
    # Memfault Interrupt blog - use main blog page
    31: "https://interrupt.memfault.com/blog/",
    32: "https://interrupt.memfault.com/blog/",
    43: "https://interrupt.memfault.com/blog/",
    60: "https://interrupt.memfault.com/blog/",
    74: "https://docs.memfault.com/docs/",
    103: "https://interrupt.memfault.com/blog/",
    137: "https://interrupt.memfault.com/blog/",
    
    # ARM TrustZone - official ARM developer
    80: "https://www.arm.com/technologies/trustzone-for-cortex-m",
    
    # Zephyr RISC-V - correct path
    59: "https://docs.zephyrproject.org/latest/boards/riscv/",
    
    # NXP docs - use main resources
    36: "https://www.nxp.com/search?keyword=watchdog&start=0",
    52: "https://www.nxp.com/products/interfaces/can-transceiver:TXCVR-CAN",
    
    # ST DMA cookbook
    47: "https://www.st.com/resource/en/application_note/an4031-using-the-stm32f2-stm32f4-and-stm32f7-series-dma-controller-stmicroelectronics.pdf",
    
    # STM32 CAN FD
    53: "https://wiki.st.com/stm32mcu/wiki/Connectivity:Introduction_to_FDCAN",
    
    # Vector LIN
    51: "https://www.vector.com/int/en/know-how/protocols/lin/",
    
    # UDS Protocol
    55: "https://www.csselectronics.com/pages/uds-protocol-tutorial-unified-diagnostic-services",
    
    # Notion templates - use main templates page
    39: "https://www.notion.so/templates/",
    125: "https://www.notion.so/templates/",
    162: "https://www.notion.so/templates/",
    
    # Technical writing
    38: "https://developers.google.com/tech-writing",
    
    # MQTT Documentation
    78: "https://mqtt.org/mqtt-specification/",
    
    # Podman/Containers
    79: "https://www.redhat.com/en/topics/containers/what-is-podman",
    
    # Safety/Compliance
    82: "https://www.iso.org/standard/68383.html",
    99: "https://www.sei.cmu.edu/research/functional-safety/",
    
    # TinyML
    87: "https://tinyml.org/",
    91: "https://mlcommons.org/benchmarks/inference-tiny/",
    96: "https://tvm.apache.org/docs/how_to/work_with_microtvm/",
    
    # Certification/Testing
    100: "https://www.absint.com/",
    107: "https://learn.adafruit.com/",
    109: "https://learn.sparkfun.com/tutorials/designing-pcbs-smd-footprints/all",
    110: "https://www.altium.com/documentation/",
    114: "https://www.ni.com/en/solutions/automated-test.html",
    120: "https://www.ul.com/services/certification",
    121: "https://ec.europa.eu/environment/topics/waste-and-recycling/rohs-directive_en",
    
    # Manufacturing
    117: "https://www.ipc.org/ContentPage.aspx?pageid=Standards",
    
    # Grafana
    70: "https://grafana.com/docs/loki/latest/",
    133: "https://grafana.com/docs/grafana/latest/alerting/",
    
    # AWS IoT
    138: "https://aws.amazon.com/iot/",
    
    # Qt for MCUs
    128: "https://www.qt.io/product/qt-for-mcus",
    
    # Career resources - use general pages
    122: "https://www.udemy.com/courses/search/?q=presentation%20skills",
    149: "https://www.freecodecamp.org/news/tag/portfolio/",
    150: "https://www.loom.com/blog",
    152: "https://github.com/search?q=embedded+systems+interview",
    154: "https://www.themuse.com/advice/star-interview-method",
    158: "https://www.atlassian.com/team-playbook",
    160: "https://www.grammarly.com/blog/thank-you-letter/",
    161: "https://www.themuse.com/advice/networking-email-templates",
    163: "https://www.linkedin.com/learning/topics/learning-and-development",
    
    # Misc
    44: "https://www.cs.cornell.edu/courses/cs4410/2022sp/schedule/papers/liu-rma.pdf",
    66: "https://www.microchip.com/en-us/products/security/secure-elements",
    101: "https://www.exida.com/resources",
    102: "https://www.mathworks.com/solutions/automotive/standards/iso-26262.html",
    111: "https://www.keysight.com/us/en/solutions/electronic-test-measurement.html",
    112: "https://www.edn.com/category/test-and-measurement/",
    113: "https://www.reliabilityeducation.com/reliabilityweb/HALT.html",
    115: "https://www.weibull.com/",
    116: "https://www.siliconexpert.com/",
    118: "https://www.assemblymag.com/topics/2667-traceability",
    123: "https://www2.deloitte.com/us/en.html",
    130: "https://developer.nvidia.com/embedded-computing",
    135: "https://www.ifixit.com/Guide",
    136: "https://www.zendesk.com/service/help-center/",
    141: "https://www.crowdstrike.com/cybersecurity-101/red-team-vs-blue-team/",
    143: "https://www.productplan.com/",
    151: "https://www.indeed.com/career-advice/",
    
    # ACM - use DOI resolver
    27: "https://dl.acm.org/",
}

def main():
    init_db()
    
    with session_scope() as session:
        updated = 0
        for rid, new_url in CORRECTIONS.items():
            resource = session.get(Resource, rid)
            if resource:
                resource.url = new_url
                session.add(resource)
                print(f"✅ ID {rid}: {resource.title[:40]}")
                updated += 1
        
        session.commit()
        print(f"\nUpdated {updated} URLs")

if __name__ == "__main__":
    main()
