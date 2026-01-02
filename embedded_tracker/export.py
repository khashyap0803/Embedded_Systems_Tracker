"""Export functionality for the Embedded Tracker application.

Provides CSV and PDF export capabilities for tasks, roadmap, and reports.
"""

from __future__ import annotations

import csv
import os
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any, List, Optional, Sequence, TypeVar, Union

from .utils import format_local_datetime, format_duration

# Setup logging
try:
    from .logging_config import setup_logging
    logger = setup_logging(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


__all__ = [
    "export_tasks_csv",
    "export_roadmap_csv",
    "export_tasks_pdf",
    "export_roadmap_pdf",
    "export_all_csv",
    "ExportError",
]


class ExportError(Exception):
    """Raised when an export operation fails."""
    pass


T = TypeVar("T")


def _safe_str(value: Any) -> str:
    """Convert any value to a safe string for CSV/PDF export."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return format_local_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return str(value)
    # Handle enum values - show just the value, not "EnumName.VALUE"
    if hasattr(value, 'value'):
        return str(value.value).replace('_', ' ').title()
    # Handle string enum representations
    result = str(value)
    if '.' in result and result.split('.')[0].endswith('Status'):
        # Extract just the status value part
        return result.split('.')[-1].replace('_', ' ').title()
    return result


def _validate_export_path(path: Union[str, Path]) -> Path:
    """Validate export path to prevent path traversal attacks.
    
    Args:
        path: The path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        ExportError: If path is invalid or contains traversal attempts
    """
    path = Path(path)
    
    # Check for path traversal attempts
    try:
        resolved = path.resolve()
    except Exception as e:
        raise ExportError(f"Invalid export path: {e}")
    
    # Ensure path string doesn't contain suspicious patterns
    path_str = str(path)
    if ".." in path_str:
        raise ExportError("Export path cannot contain '..' (path traversal not allowed)")
    
    # Ensure parent directory exists or can be created
    parent = resolved.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ExportError(f"Cannot create export directory: {e}")
    
    return resolved


def export_tasks_csv(
    tasks: Sequence[Any],
    output_path: Optional[Union[str, Path]] = None,
) -> str:
    """Export tasks to CSV format.
    
    Args:
        tasks: Sequence of TaskRecord objects
        output_path: Optional file path. If None, returns CSV as string.
    
    Returns:
        CSV content as string (also written to file if path provided)
    
    Raises:
        ExportError: If export fails
    """
    try:
        columns = [
            ("ID", "id"),
            ("Title", "title"),
            ("Status", "status"),
            ("Week", "week_number"),
            ("Day", "day_number"),
            ("Hour", "hour_number"),
            ("Est. Hours", "estimated_hours"),
            ("Work Time", "work_seconds"),
            ("Break Time", "break_seconds"),
            ("First Started", "first_started_at"),
            ("Completed", "completed_at"),
        ]
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([col[0] for col in columns])
        
        # Data rows
        for task in tasks:
            row = []
            for _, attr in columns:
                value = getattr(task, attr, None)
                if attr in ("work_seconds", "break_seconds"):
                    row.append(format_duration(value))
                else:
                    row.append(_safe_str(value))
            writer.writerow(row)
        
        csv_content = output.getvalue()
        
        if output_path:
            path = _validate_export_path(output_path)
            path.write_text(csv_content, encoding="utf-8")
        
        return csv_content
        
    except ExportError:
        raise
    except Exception as e:
        raise ExportError(f"Failed to export tasks to CSV: {e}") from e


def export_roadmap_csv(
    phases: Sequence[Any],
    weeks: Sequence[Any],
    output_path: Optional[Union[str, Path]] = None,
) -> str:
    """Export roadmap overview to CSV format.
    
    Args:
        phases: Sequence of PhaseRecord objects
        weeks: Sequence of WeekRecord objects
        output_path: Optional file path
    
    Returns:
        CSV content as string
    """
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        # Phases section
        writer.writerow(["=== PHASES ==="])
        writer.writerow(["ID", "Name", "Status", "Start", "End", "Work Hours"])
        for phase in phases:
            writer.writerow([
                _safe_str(phase.id),
                _safe_str(phase.name),
                _safe_str(phase.status),
                _safe_str(phase.start_date),
                _safe_str(phase.end_date),
                f"{phase.work_hours:.1f}" if hasattr(phase, 'work_hours') else "",
            ])
        
        writer.writerow([])
        
        # Weeks section
        writer.writerow(["=== WEEKS ==="])
        writer.writerow(["Week #", "Phase", "Focus", "Status", "Start", "End", "Work Hours"])
        for week in weeks:
            writer.writerow([
                _safe_str(week.number),
                _safe_str(week.phase_name),
                _safe_str(getattr(week, 'focus', '')),
                _safe_str(week.status),
                _safe_str(week.start_date),
                _safe_str(week.end_date),
                f"{week.work_hours:.1f}" if hasattr(week, 'work_hours') else "",
            ])
        
        csv_content = output.getvalue()
        
        if output_path:
            path = _validate_export_path(output_path)
            path.write_text(csv_content, encoding="utf-8")
        
        return csv_content
        
    except ExportError:
        raise
    except Exception as e:
        raise ExportError(f"Failed to export roadmap to CSV: {e}") from e


def export_tasks_pdf(
    tasks: Sequence[Any],
    output_path: Union[str, Path],
    title: str = "Tasks Report",
) -> Path:
    """Export tasks to PDF format.
    
    Args:
        tasks: Sequence of TaskRecord objects
        output_path: File path for PDF output
        title: Report title
    
    Returns:
        Path to created PDF file
    
    Raises:
        ExportError: If PDF generation fails or reportlab not installed
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
        )
    except ImportError:
        raise ExportError(
            "PDF export requires reportlab. Install with: pip install reportlab"
        )
    
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(
            str(path),
            pagesize=landscape(A4),
            rightMargin=0.4*inch,
            leftMargin=0.4*inch,
            topMargin=0.4*inch,
            bottomMargin=0.4*inch,
        )
        
        styles = getSampleStyleSheet()
        
        # Create custom styles for table cells with word wrap
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            wordWrap='CJK',
        )
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke,
            fontName='Helvetica-Bold',
        )
        
        elements: List[Any] = []
        
        # Title
        elements.append(Paragraph(title, styles["Title"]))
        elements.append(Spacer(1, 0.2*inch))
        
        # Table headers with Paragraph for consistency
        headers = [
            Paragraph("ID", header_style),
            Paragraph("Title", header_style),
            Paragraph("Status", header_style),
            Paragraph("Week", header_style),
            Paragraph("Work Time", header_style),
            Paragraph("Started", header_style),
            Paragraph("Completed", header_style),
        ]
        data = [headers]
        
        for task in tasks:
            # Truncate title if too long but allow some wrapping
            task_title = task.title
            if len(task_title) > 60:
                task_title = task_title[:57] + "..."
            
            data.append([
                Paragraph(str(task.id), cell_style),
                Paragraph(task_title, cell_style),
                Paragraph(str(task.status.value if hasattr(task.status, 'value') else task.status), cell_style),
                Paragraph(str(task.week_number), cell_style),
                Paragraph(format_duration(task.work_seconds), cell_style),
                Paragraph(format_local_datetime(task.first_started_at, "%d/%m/%y"), cell_style),
                Paragraph(format_local_datetime(task.completed_at, "%d/%m/%y"), cell_style),
            ])
        
        # Better column widths - more space for Title
        col_widths = [0.4*inch, 4.5*inch, 0.8*inch, 0.5*inch, 0.8*inch, 0.8*inch, 0.8*inch]
        table = Table(data, repeatRows=1, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        return path
        
    except Exception as e:
        logger.exception("PDF generation failed")
        raise ExportError(f"PDF generation failed: {str(e)}") from e




def export_roadmap_pdf(
    phases: Sequence[Any],
    weeks: Sequence[Any],
    output_path: Union[str, Path],
    title: str = "Embedded Systems Roadmap",
) -> Path:
    """Export full roadmap to PDF format.
    
    Args:
        phases: Sequence of PhaseRecord objects
        weeks: Sequence of WeekRecord objects
        output_path: File path for PDF output
        title: Report title
    
    Returns:
        Path to created PDF file
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
        )
    except ImportError:
        raise ExportError(
            "PDF export requires reportlab. Install with: pip install reportlab"
        )
    
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use landscape for more horizontal space
        doc = SimpleDocTemplate(
            str(path),
            pagesize=landscape(A4),
            rightMargin=0.4*inch,
            leftMargin=0.4*inch,
            topMargin=0.4*inch,
            bottomMargin=0.4*inch,
        )
        
        styles = getSampleStyleSheet()
        
        # Create custom styles for table cells with word wrap
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            wordWrap='CJK',  # Enable word wrap
        )
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.whitesmoke,
            fontName='Helvetica-Bold',
        )
        
        elements: List[Any] = []
        
        # Title
        elements.append(Paragraph(title, styles["Title"]))
        elements.append(Spacer(1, 0.2*inch))
        
        # Phases table with wrapped text
        elements.append(Paragraph("Phases Overview", styles["Heading2"]))
        elements.append(Spacer(1, 0.1*inch))
        
        phase_headers = [
            Paragraph("ID", header_style),
            Paragraph("Name", header_style),
            Paragraph("Status", header_style),
            Paragraph("Start", header_style),
            Paragraph("End", header_style),
        ]
        phase_data = [phase_headers]
        
        for phase in phases:
            phase_data.append([
                Paragraph(str(phase.id), cell_style),
                Paragraph(phase.name, cell_style),
                Paragraph(str(phase.status.value if hasattr(phase.status, 'value') else phase.status), cell_style),
                Paragraph(str(phase.start_date), cell_style),
                Paragraph(str(phase.end_date), cell_style),
            ])
        
        # Wider column widths for phase name
        phase_col_widths = [0.4*inch, 4.5*inch, 0.8*inch, 1*inch, 1*inch]
        phase_table = Table(phase_data, repeatRows=1, colWidths=phase_col_widths)
        phase_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(phase_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Weeks summary with proper wrapping
        elements.append(Paragraph("Weekly Schedule", styles["Heading2"]))
        elements.append(Spacer(1, 0.1*inch))
        
        week_headers = [
            Paragraph("Wk", header_style),
            Paragraph("Phase", header_style),
            Paragraph("Focus", header_style),
            Paragraph("Status", header_style),
        ]
        week_data = [week_headers]
        
        for week in weeks:
            focus = getattr(week, 'focus', '') or ''
            # Truncate very long focus text but allow wrapping
            if len(focus) > 80:
                focus = focus[:77] + "..."
            week_data.append([
                Paragraph(str(week.number), cell_style),
                Paragraph(week.phase_name, cell_style),
                Paragraph(focus, cell_style),
                Paragraph(str(week.status.value if hasattr(week.status, 'value') else week.status), cell_style),
            ])
        
        # Better column widths - more space for Focus column
        week_col_widths = [0.4*inch, 1.8*inch, 5*inch, 0.8*inch]
        week_table = Table(week_data, repeatRows=1, colWidths=week_col_widths)
        week_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27ae60")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eafaf1")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(week_table)
        
        # Build PDF
        doc.build(elements)
        
        return path
        
    except Exception as e:
        logger.exception("PDF generation failed")
        raise ExportError(f"PDF generation failed: {str(e)}") from e


def export_all_csv(output_folder: Union[str, Path]) -> dict:
    """Export all database tables to CSV files in a folder.
    
    Creates individual CSV files for each table plus a combined all.csv file.
    
    Args:
        output_folder: Path to folder where CSV files will be created
        
    Returns:
        Dictionary with export statistics for each table
        
    Raises:
        ExportError: If export fails
    """
    from . import services
    
    try:
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        
        stats = {}
        all_data = []  # For combined all.csv
        
        # 1. Export Phases
        phases = services.list_phases()
        with open(folder / "phases.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Description", "Status", "Start Date", "End Date"])
            for p in phases:
                writer.writerow([
                    p.id, p.name, getattr(p, 'description', ''),
                    _safe_str(p.status), _safe_str(p.start_date), _safe_str(p.end_date)
                ])
        stats["phases"] = len(phases)
        all_data.append(("=== PHASES ===", ["ID", "Name", "Description", "Status", "Start Date", "End Date"], 
                        [[p.id, p.name, getattr(p, 'description', ''), _safe_str(p.status), 
                          _safe_str(p.start_date), _safe_str(p.end_date)] for p in phases]))
        
        # 2. Export Weeks
        weeks = services.list_weeks()
        with open(folder / "weeks.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Number", "Phase", "Focus", "Status", "Start Date", "End Date"])
            for w in weeks:
                writer.writerow([
                    w.id, w.number, w.phase_name, getattr(w, 'focus', ''),
                    _safe_str(w.status), _safe_str(w.start_date), _safe_str(w.end_date)
                ])
        stats["weeks"] = len(weeks)
        all_data.append(("=== WEEKS ===", ["ID", "Number", "Phase", "Focus", "Status", "Start Date", "End Date"],
                        [[w.id, w.number, w.phase_name, getattr(w, 'focus', ''), _safe_str(w.status),
                          _safe_str(w.start_date), _safe_str(w.end_date)] for w in weeks]))
        
        # 3. Export Days
        days = services.list_days()
        with open(folder / "days.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Number", "Week", "Focus", "Status", "Scheduled Date"])
            for d in days:
                writer.writerow([
                    d.id, d.number, d.week_number, d.focus,
                    _safe_str(d.status), _safe_str(d.scheduled_date)
                ])
        stats["days"] = len(days)
        all_data.append(("=== DAYS ===", ["ID", "Number", "Week", "Focus", "Status", "Scheduled Date"],
                        [[d.id, d.number, d.week_number, d.focus, _safe_str(d.status),
                          _safe_str(d.scheduled_date)] for d in days]))
        
        # 4. Export Tasks
        tasks = services.list_tasks()
        with open(folder / "tasks.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "Week", "Day", "Hour", "Status", "Work Seconds", "Break Seconds"])
            for t in tasks:
                writer.writerow([
                    t.id, t.title, t.week_number, t.day_number, t.hour_number,
                    _safe_str(t.status), t.work_seconds, t.break_seconds
                ])
        stats["tasks"] = len(tasks)
        all_data.append(("=== TASKS ===", ["ID", "Title", "Week", "Day", "Hour", "Status", "Work Seconds", "Break Seconds"],
                        [[t.id, t.title, t.week_number, t.day_number, t.hour_number,
                          _safe_str(t.status), t.work_seconds, t.break_seconds] for t in tasks]))
        
        # 5. Export Resources
        resources = services.list_resources()
        with open(folder / "resources.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "Type", "URL", "Week", "Phase", "Notes"])
            for r in resources:
                writer.writerow([
                    r.id, r.title, _safe_str(r.type), r.url,
                    r.week_number, r.phase_name, r.notes
                ])
        stats["resources"] = len(resources)
        all_data.append(("=== RESOURCES ===", ["ID", "Title", "Type", "URL", "Week", "Phase", "Notes"],
                        [[r.id, r.title, _safe_str(r.type), r.url, r.week_number, r.phase_name, r.notes] for r in resources]))
        
        # 6. Export Projects
        projects = services.list_projects()
        with open(folder / "projects.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Status", "Phase", "Repo URL", "Due Date"])
            for p in projects:
                writer.writerow([
                    p.id, p.name, _safe_str(p.status), p.phase_name,
                    p.repo_url, _safe_str(p.due_date)
                ])
        stats["projects"] = len(projects)
        all_data.append(("=== PROJECTS ===", ["ID", "Name", "Status", "Phase", "Repo URL", "Due Date"],
                        [[p.id, p.name, _safe_str(p.status), p.phase_name, p.repo_url, _safe_str(p.due_date)] for p in projects]))
        
        # 7. Export Certifications
        certifications = services.list_certifications()
        with open(folder / "certifications.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Provider", "Status", "Progress", "Due Date"])
            for c in certifications:
                writer.writerow([
                    c.id, c.name, c.provider, _safe_str(c.status),
                    c.progress, _safe_str(c.due_date)
                ])
        stats["certifications"] = len(certifications)
        all_data.append(("=== CERTIFICATIONS ===", ["ID", "Name", "Provider", "Status", "Progress", "Due Date"],
                        [[c.id, c.name, c.provider, _safe_str(c.status), c.progress, _safe_str(c.due_date)] for c in certifications]))
        
        # 8. Export Applications
        applications = services.list_applications()
        with open(folder / "applications.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Company", "Role", "Status", "Date Applied", "Next Action"])
            for a in applications:
                writer.writerow([
                    a.id, a.company, a.role, _safe_str(a.status),
                    _safe_str(a.date_applied), a.next_action
                ])
        stats["applications"] = len(applications)
        all_data.append(("=== APPLICATIONS ===", ["ID", "Company", "Role", "Status", "Date Applied", "Next Action"],
                        [[a.id, a.company, a.role, _safe_str(a.status), _safe_str(a.date_applied), a.next_action] for a in applications]))
        
        # 9. Export Hardware
        hardware = services.list_hardware()
        with open(folder / "hardware.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Category", "Status", "Quantity", "Price INR", "Notes"])
            for h in hardware:
                writer.writerow([
                    h.id, h.name, _safe_str(h.category), _safe_str(h.status),
                    h.quantity, h.price_inr, h.notes
                ])
        stats["hardware"] = len(hardware)
        all_data.append(("=== HARDWARE ===", ["ID", "Name", "Category", "Status", "Quantity", "Price INR", "Notes"],
                        [[h.id, h.name, _safe_str(h.category), _safe_str(h.status), h.quantity, h.price_inr, h.notes] for h in hardware]))
        
        # 10. Create combined all.csv
        with open(folder / "all.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Embedded Tracker - Complete Database Export"])
            writer.writerow([f"Generated: {datetime.now().isoformat()}"])
            writer.writerow([])
            
            for section_name, headers, rows in all_data:
                writer.writerow([section_name])
                writer.writerow(headers)
                for row in rows:
                    writer.writerow(row)
                writer.writerow([])  # Empty row between sections
        
        stats["total_records"] = sum(stats.values())
        stats["files_created"] = 10  # 9 individual + 1 all.csv
        
        logger.info(f"Exported all data to {folder}: {stats}")
        return stats
        
    except Exception as e:
        logger.exception("Export all failed")
        raise ExportError(f"Failed to export all data: {e}") from e
