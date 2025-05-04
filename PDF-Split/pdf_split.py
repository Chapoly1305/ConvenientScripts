import os
import re
import argparse
from PyPDF2 import PdfReader, PdfWriter


def extract_bookmarks_from_pdf(pdf_path, verbose=True):
    """Extract all bookmarks from a PDF file with verbose output."""
    print(f"Analyzing PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    bookmarks = []

    # Process bookmarks recursively
    def process_bookmark(item):
        if isinstance(item, dict) and '/Title' in item:
            title = item['/Title']
            try:
                page_num = reader.get_destination_page_number(item)
                bookmarks.append({
                    'title': title,
                    'page': page_num
                })
            except Exception as e:
                print(f"Error processing bookmark '{title}': {e}")
        elif isinstance(item, list):
            for subitem in item:
                process_bookmark(subitem)

    # Process all bookmarks
    for item in reader.outline:
        process_bookmark(item)

    # Sort by page number
    bookmarks.sort(key=lambda b: b['page'])

    if verbose:
        print(f"Found {len(bookmarks)} bookmarks")
        if bookmarks:
            print("\nSample bookmarks:")
            for i, bm in enumerate(bookmarks[:10]):  # Show first 10 bookmarks
                print(f"{i + 1}. '{bm['title']}' (Page {bm['page'] + 1})")

    return bookmarks, reader


def extract_section_info(title):
    """
    Extract chapter and section information from bookmark title.
    Returns (chapter_num, section_id, section_title, level)
    """
    # Try different patterns to match various title formats

    # Pattern 1: Chapter with number (e.g., "Chapter 1: Introduction")
    chapter_match = re.match(r'Chapter\s+(\d+)[:\.]?\s+(.*)', title)
    if chapter_match:
        return (chapter_match.group(1), None, chapter_match.group(2), 0)

    # Pattern 2: Section with X.Y format (e.g., "1.1 Overview")
    section_match = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?\s+(.*)', title)
    if section_match:
        chapter_num = section_match.group(1)
        section_num = section_match.group(2)
        subsection_num = section_match.group(3)
        subsubsection_num = section_match.group(4)

        section_title = section_match.group(5)

        if subsubsection_num:
            # Level 3: X.Y.Z.W
            section_id = f"{chapter_num}.{section_num}.{subsection_num}.{subsubsection_num}"
            return (chapter_num, section_id, section_title, 3)
        elif subsection_num:
            # Level 2: X.Y.Z
            section_id = f"{chapter_num}.{section_num}.{subsection_num}"
            return (chapter_num, section_id, section_title, 2)
        else:
            # Level 1: X.Y
            section_id = f"{chapter_num}.{section_num}"
            return (chapter_num, section_id, section_title, 1)

    # Pattern 3: Just a number at the beginning (e.g., "1 Introduction")
    simple_match = re.match(r'(\d+)\s+(.*)', title)
    if simple_match:
        return (simple_match.group(1), simple_match.group(1), simple_match.group(2), 0)

    # Pattern 4: Just X.Y at the beginning without space (e.g., "1.1Overview")
    compact_match = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?(.*)', title)
    if compact_match:
        chapter_num = compact_match.group(1)
        section_num = compact_match.group(2)
        subsection_num = compact_match.group(3)
        subsubsection_num = compact_match.group(4)

        section_title = compact_match.group(5)

        if subsubsection_num:
            # Level 3: X.Y.Z.W
            section_id = f"{chapter_num}.{section_num}.{subsection_num}.{subsubsection_num}"
            return (chapter_num, section_id, section_title, 3)
        elif subsection_num:
            # Level 2: X.Y.Z
            section_id = f"{chapter_num}.{section_num}.{subsection_num}"
            return (chapter_num, section_id, section_title, 2)
        else:
            # Level 1: X.Y
            section_id = f"{chapter_num}.{section_num}"
            return (chapter_num, section_id, section_title, 1)

    # Pattern 5: Appendix style (e.g., "Appendix A: References")
    appendix_match = re.match(r'Appendix\s+([A-Z])[:\.]?\s+(.*)', title)
    if appendix_match:
        return (f"App{appendix_match.group(1)}", None, appendix_match.group(2), 0)

    # No recognizable pattern
    return (None, None, None, -1)


def create_clean_filename(text):
    """Create a clean filename from text."""
    if not text:
        return "Unnamed"

    # Replace invalid characters
    clean = re.sub(r'[\\/*?:"<>|]', '_', text)
    # Replace multiple spaces with single underscore
    clean = re.sub(r'\s+', '_', clean)
    # Limit length and trim
    return clean.strip('_')[:80]


def hierarchy_split_pdf(pdf_path, output_dir=None, min_level=1, max_level=1):
    """Split PDF into hierarchy of folders with chapters and sections."""
    # Get base name for root folder
    pdf_basename = os.path.basename(pdf_path)
    base_filename = os.path.splitext(pdf_basename)[0]

    # Set root output directory
    if output_dir:
        root_dir = os.path.join(output_dir, base_filename)
    else:
        root_dir = os.path.join(os.path.dirname(pdf_path) or '.', base_filename)

    # Extract bookmarks and reader
    bookmarks, reader = extract_bookmarks_from_pdf(pdf_path)

    # Process bookmarks to identify chapters and sections
    chapters = {}  # Store chapter info
    chapter_titles = {}  # Store chapter titles
    sections = []  # Store section info

    # First pass: Find chapters and sections
    for bm in bookmarks:
        chapter_num, section_id, section_title, level = extract_section_info(bm['title'])

        if not chapter_num:
            print(f"Skipping unrecognized bookmark: '{bm['title']}'")
            continue

        if level == 0:
            # It's a chapter
            chapters[chapter_num] = {
                'title': bm['title'],
                'page': bm['page']
            }
            chapter_titles[chapter_num] = section_title
        elif min_level <= level <= max_level:
            # It's a section at our target level
            sections.append({
                'title': bm['title'],
                'chapter': chapter_num,
                'section': section_id,
                'section_title': section_title,
                'page': bm['page'],
                'level': level
            })

    print(f"\nIdentified {len(chapters)} chapters and {len(sections)} sections (levels {min_level}-{max_level})")

    # If we have chapters but no sections, try adjusting the level
    if len(chapters) > 0 and len(sections) == 0:
        print("No sections found at specified levels. Trying alternative patterns...")

        # Second attempt: Try treating chapters as sections
        if len(chapters) > 1:
            for chapter_num, chapter in chapters.items():
                sections.append({
                    'title': chapter['title'],
                    'chapter': '0',  # Main document chapter
                    'section': chapter_num,
                    'section_title': chapter_titles.get(chapter_num, ''),
                    'page': chapter['page'],
                    'level': 0  # Chapter level
                })

            print(f"Using {len(sections)} chapters as sections instead")
        else:
            print("Not enough chapters to use as sections")

    # Sort sections by page number
    sections.sort(key=lambda s: s['page'])

    # Calculate page ranges for sections
    section_ranges = []
    for i, section in enumerate(sections):
        start_page = section['page']

        # End page is either before the next section or the end of the PDF
        if i < len(sections) - 1:
            end_page = sections[i + 1]['page'] - 1
        else:
            end_page = len(reader.pages) - 1

        section_ranges.append({
            'title': section['title'],
            'chapter': section['chapter'],
            'section': section['section'],
            'section_title': section['section_title'],
            'start': start_page,
            'end': end_page
        })

    if not section_ranges:
        print("No sections to split!")
        return

    # Create PDFs for each section
    for section in section_ranges:
        # Create chapter directory with name
        chapter_num = section['chapter']
        chapter_title = chapter_titles.get(chapter_num, "Chapter_" + chapter_num)
        chapter_folder_name = f"Chapter_{chapter_num}_{create_clean_filename(chapter_title)}"
        chapter_dir = os.path.join(root_dir, chapter_folder_name)

        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        # Create PDF writer
        writer = PdfWriter()

        # Add pages for this section
        for page_num in range(section['start'], section['end'] + 1):
            writer.add_page(reader.pages[page_num])

        # Create section filename
        section_id = section['section'].replace('.', '_') if section['section'] else f"Section_{section['chapter']}"
        clean_title = create_clean_filename(section['section_title'])

        output_filename = f"{section_id}_{clean_title}.pdf"
        output_path = os.path.join(chapter_dir, output_filename)

        # Write the file
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        print(f"Created: {output_path} (Pages {section['start'] + 1}-{section['end'] + 1})")

    print(
        f"Split {len(section_ranges)} sections across {len(set(s['chapter'] for s in section_ranges))} chapters in '{root_dir}'")


def main():
    parser = argparse.ArgumentParser(description='Split PDF into chapter and section folders.')
    parser.add_argument('input_pdf', help='Path to the input PDF file')
    parser.add_argument('-o', '--output-dir', help='Output directory (default: same as input)')
    parser.add_argument('--min-level', type=int, default=1, help='Minimum section level to extract (default: 1)')
    parser.add_argument('--max-level', type=int, default=1, help='Maximum section level to extract (default: 1)')
    args = parser.parse_args()

    hierarchy_split_pdf(args.input_pdf, args.output_dir, args.min_level, args.max_level)


if __name__ == "__main__":
    main()