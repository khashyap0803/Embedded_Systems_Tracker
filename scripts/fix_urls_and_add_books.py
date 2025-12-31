#!/usr/bin/env python3
"""Fix remaining broken URLs and add book resources"""

from embedded_tracker.db import session_scope, init_db
from embedded_tracker.models import Resource, Week
from sqlmodel import select

# Final URL corrections for truly broken URLs
URL_FIXES = {
    # Practical Electronics - use official publisher
    2: "https://www.mhprofessional.com/practical-electronics-for-inventors-fourth-edition-9781259587542-usa",
    
    # edX C Programming - use alternative
    13: "https://www.edx.org/learn/c-programming",
    
    # Embedded C Coding Standards - Barr Group main page
    17: "https://barrgroup.com/embedded-systems/books",
    
    # STM32 Reference Manual - use main ST documentation page
    18: "https://www.st.com/en/microcontrollers-microprocessors/stm32f7-series/documentation.html",
    
    # I2C Bus Specification - official NXP
    19: "https://www.nxp.com/docs/en/user-guide/UM10204.pdf",
    
    # minicom cheat-sheet - use GNU documentation
    21: "https://linux.die.net/man/1/minicom",
    
    # GeeksforGeeks quiz - use main electronics page
    22: "https://www.geeksforgeeks.org/electronics-engineering/",
    
    # Otii scripting - use main Qoitech page
    26: "https://www.qoitech.com/",
    
    # NXP watchdog - use main application notes
    36: "https://www.nxp.com/design/application-notes:APNOTES",
    
    # Liu & Layland RMA paper - use IEEE or alternative
    44: "https://ieeexplore.ieee.org/document/1451669",
    
    # Vector LIN - use main know-how page
    51: "https://www.vector.com/int/en/know-how/",
    
    # NXP CAN - use main CAN page
    52: "https://www.nxp.com/products/interfaces/can-transceivers:CAN",
    
    # Zephyr RISC-V - use main boards page
    59: "https://docs.zephyrproject.org/latest/boards/",
    
    # Memfault docs - use main docs
    74: "https://docs.memfault.com/",
    
    # TVM microTVM - use main docs
    96: "https://tvm.apache.org/docs/",
    
    # SEI Functional Safety - use main research page
    99: "https://www.sei.cmu.edu/",
    
    # HALT/HASS - use reliability web
    113: "https://www.weibull.com/basics/accelerated.htm",
    
    # NI Testing - use main NI page
    114: "https://www.ni.com/en/solutions.html",
    
    # Qt for MCUs - use main Qt page
    128: "https://www.qt.io/qt-for-embedded-development",
    
    # Grammarly thank you - use main blog
    160: "https://www.grammarly.com/blog/",
    
    # The Muse networking - use main career advice
    161: "https://www.themuse.com/advice",
}

# Best books to add for each phase/topic
BOOKS_TO_ADD = [
    # Phase 1: Foundations
    {
        'title': 'Practical Electronics for Inventors (4th Ed) - Paul Scherz',
        'url': 'https://www.amazon.com/Practical-Electronics-Inventors-Fourth-Scherz/dp/1259587541',
        'type': 'book',
        'week_id': 1,  # Week 1
        'notes': 'Essential reference for electronics fundamentals'
    },
    {
        'title': 'The Art of Electronics (3rd Ed) - Horowitz & Hill',
        'url': 'https://www.amazon.com/Art-Electronics-Paul-Horowitz/dp/0521809266',
        'type': 'book',
        'week_id': 1,
        'notes': 'The bible of electronics - comprehensive reference'
    },
    {
        'title': 'The C Programming Language (K&R) - Kernighan & Ritchie',
        'url': 'https://www.amazon.com/Programming-Language-2nd-Brian-Kernighan/dp/0131103628',
        'type': 'book',
        'week_id': 3,  # C Programming week
        'notes': 'The definitive C language book by its creators'
    },
    {
        'title': 'Embedded C Coding Standard - Barr Group',
        'url': 'https://www.amazon.com/Embedded-Coding-Standard-Michael-Barr/dp/1442164824',
        'type': 'book',
        'week_id': 3,
        'notes': 'Industry coding standards for embedded C'
    },
    {
        'title': 'Definitive Guide to ARM Cortex-M3/M4 - Joseph Yiu',
        'url': 'https://www.amazon.com/Definitive-Guide-ARM-Cortex-M3/dp/0124080820',
        'type': 'book',
        'week_id': 5,  # GPIO/Registers week
        'notes': 'Essential ARM Cortex-M architecture reference'
    },
    {
        'title': 'Mastering STM32 (2nd Ed) - Carmine Noviello',
        'url': 'https://leanpub.com/mastering-stm32',
        'type': 'book',
        'week_id': 5,
        'notes': 'Comprehensive STM32 development guide'
    },
    {
        'title': 'Making Embedded Systems - Elecia White',
        'url': 'https://www.amazon.com/Making-Embedded-Systems-Patterns-Software/dp/1098151542',
        'type': 'book',
        'week_id': 7,  # DMA week
        'notes': 'Design patterns for embedded software'
    },
    # Phase 2: Professional
    {
        'title': 'Designing Embedded Hardware - John Catsoulis',
        'url': 'https://www.amazon.com/Designing-Embedded-Hardware-John-Catsoulis/dp/0596007558',
        'type': 'book',
        'week_id': 15,  # Board bring-up
        'notes': 'Hardware design for embedded systems'
    },
    {
        'title': 'Real-Time Concepts for Embedded Systems - Qing Li',
        'url': 'https://www.amazon.com/Real-Time-Concepts-Embedded-Systems-Li/dp/1578201241',
        'type': 'book',
        'week_id': 20,  # RTOS week
        'notes': 'RTOS fundamentals and real-time programming'
    },
    {
        'title': 'TinyML - Pete Warden & Daniel Situnayake',
        'url': 'https://www.amazon.com/TinyML-Learning-TensorFlow-Ultra-Low-Micro-Controllers/dp/1492052043',
        'type': 'book',
        'week_id': 35,  # TinyML week
        'notes': 'Machine learning on microcontrollers'
    },
    # Phase 3: Advanced
    {
        'title': 'Embedded Systems Security - David Kleidermacher',
        'url': 'https://www.amazon.com/Embedded-Systems-Security-Practical-Approaches/dp/1493939939',
        'type': 'book',
        'week_id': 25,  # Security week
        'notes': 'Security for embedded systems'
    },
    {
        'title': 'The Linux Command Line (2nd Ed) - William Shotts',
        'url': 'https://www.amazon.com/Linux-Command-Line-Complete-Introduction/dp/1593279523',
        'type': 'book',
        'week_id': 30,  # Linux week
        'notes': 'Essential Linux command line reference'
    },
]

def main():
    init_db()
    
    with session_scope() as session:
        # Fix broken URLs
        print("Fixing broken URLs...")
        for rid, new_url in URL_FIXES.items():
            resource = session.get(Resource, rid)
            if resource:
                resource.url = new_url
                session.add(resource)
                print(f"  ✅ ID {rid}: {resource.title[:40]}")
        
        print(f"\nFixed {len(URL_FIXES)} URLs")
        
        # Add book resources
        print("\nAdding book resources...")
        from embedded_tracker.models import ResourceType
        
        for book in BOOKS_TO_ADD:
            # Check if book already exists
            existing = session.exec(
                select(Resource).where(Resource.title == book['title'])
            ).first()
            
            if not existing:
                resource = Resource(
                    title=book['title'],
                    url=book['url'],
                    type=ResourceType.OTHER,
                    notes=book['notes'],
                    week_id=book['week_id']
                )
                session.add(resource)
                print(f"  📚 Added: {book['title'][:50]}")
            else:
                print(f"  ⏭️  Exists: {book['title'][:50]}")
        
        session.commit()
        print(f"\nAdded {len(BOOKS_TO_ADD)} book resources")
        print("Done!")

if __name__ == "__main__":
    main()
