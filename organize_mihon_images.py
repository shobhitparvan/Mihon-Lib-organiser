#!/usr/bin/env python3
"""
Mihon Image Folder Organizer Script
This script organizes folders containing images into Mihon's local directory structure
Each folder becomes a manga title with images organized into chapters
"""

import os
import shutil
import argparse
import re
import math
from pathlib import Path
from typing import List, Tuple, Optional
import sys


def get_safe_folder_name(name: str) -> str:
    """Sanitize folder names for filesystem compatibility"""
    # Remove invalid characters for Windows filesystem
    invalid_chars = r'[<>:"/\\|?*]'
    safe_name = re.sub(invalid_chars, '_', name)
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Limit length to avoid path length issues
    if len(safe_name) > 100:
        safe_name = safe_name[:100]
    
    return safe_name


def get_image_files(path: str) -> List[Path]:
    """Get all image files recursively from a directory"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    
    path_obj = Path(path)
    images = []
    
    for file_path in path_obj.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            images.append(file_path)
    
    return sorted(images, key=lambda x: x.name)


def format_chapter_name(chapter_number: int) -> str:
    """Format chapter folder name"""
    return f"Chapter {chapter_number:03d}"


def organize_images_into_chapters(manga_path: str, image_files: List[Path], 
                                images_per_chapter: Optional[int], dry_run: bool) -> None:
    """Organize images into chapter folders"""
    total_images = len(image_files)
    
    # If images_per_chapter is None, put all images in Chapter 1
    if images_per_chapter is None:
        total_chapters = 1
        images_per_chapter = total_images
        print(f"    Total images: {total_images}")
        print(f"    Will create 1 chapter with all {total_images} images")
    else:
        total_chapters = math.ceil(total_images / images_per_chapter)
        print(f"    Total images: {total_images}")
        print(f"    Will create {total_chapters} chapters ({images_per_chapter} images per chapter)")
    
    for chapter_num in range(1, total_chapters + 1):
        chapter_name = format_chapter_name(chapter_num)
        chapter_path = Path(manga_path) / chapter_name
        
        start_index = (chapter_num - 1) * images_per_chapter
        end_index = min(start_index + images_per_chapter, total_images)
        chapter_images = image_files[start_index:end_index]
        
        print(f"    Creating {chapter_name} with {len(chapter_images)} images")
        
        if not dry_run:
            # Create chapter directory
            chapter_path.mkdir(parents=True, exist_ok=True)
            
            # Move images to chapter folder
            for image in chapter_images:
                dest_path = chapter_path / image.name
                
                # Handle duplicate names
                counter = 1
                original_name = image.name
                while dest_path.exists():
                    name_without_ext = Path(original_name).stem
                    extension = Path(original_name).suffix
                    new_name = f"{name_without_ext}_{counter}{extension}"
                    dest_path = chapter_path / new_name
                    counter += 1
                
                try:
                    shutil.move(str(image), str(dest_path))
                except Exception as e:
                    print(f"      Error moving {image.name}: {e}")


def remove_empty_directories(path: str) -> None:
    """Remove empty directories recursively"""
    path_obj = Path(path)
    
    while True:
        empty_dirs = []
        for dir_path in path_obj.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                empty_dirs.append(dir_path)
        
        if not empty_dirs:
            break
            
        for dir_path in empty_dirs:
            try:
                dir_path.rmdir()
                print(f"      Removed empty directory: {dir_path.name}")
            except Exception as e:
                print(f"      Could not remove empty directory {dir_path.name}: {e}")


def organize_mihon_image_folders(source_path: str, images_per_chapter: Optional[int], 
                               dry_run: bool, in_place: bool) -> None:
    """Main organization function"""
    print("Starting Mihon image folder organization...")
    print(f"Source Path: {source_path}")
    if images_per_chapter is None:
        print("Images per chapter: All images in Chapter 1")
    else:
        print(f"Images per chapter: {images_per_chapter}")
    print(f"In-place organization: {in_place}")
    
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    
    source_path_obj = Path(source_path)
    
    # Get all directories in source path (these will be manga titles)
    manga_directories = [d for d in source_path_obj.iterdir() 
                        if d.is_dir() and not re.match(r'^(Organized_Mihon|_Backup)$', d.name)]
    
    if not manga_directories:
        print("No manga directories found in source path.")
        return
    
    print(f"Found {len(manga_directories)} manga directories to process\n")
    
    # Create backup if not in-place and not dry run
    if not in_place and not dry_run:
        backup_path = source_path_obj / "_Backup"
        if not backup_path.exists():
            backup_path.mkdir(parents=True, exist_ok=True)
            print(f"Created backup directory: {backup_path}")
    
    for manga_dir in manga_directories:
        manga_title = get_safe_folder_name(manga_dir.name)
        print(f"Processing manga: {manga_title}")
        
        # Get all image files in this manga directory
        image_files = get_image_files(str(manga_dir))
        
        if not image_files:
            print(f"  No image files found in {manga_title}, skipping...")
            continue
        
        if in_place:
            # Organize in the same directory
            target_path = manga_dir
            
            # Create backup of original structure if not dry run
            if not dry_run:
                backup_path = source_path_obj / "_Backup"
                manga_backup_path = backup_path / manga_title
                if not manga_backup_path.exists():
                    shutil.copytree(str(manga_dir), str(manga_backup_path))
                    print("  Created backup of original structure")
        else:
            # Create organized version in new location
            organized_path = source_path_obj / "Organized_Mihon"
            target_path = organized_path / manga_title
            
            if not dry_run:
                organized_path.mkdir(parents=True, exist_ok=True)
                target_path.mkdir(parents=True, exist_ok=True)
                
                # Copy all images to target location first
                for image in image_files:
                    dest_path = target_path / image.name
                    
                    # Handle duplicate names
                    counter = 1
                    original_name = image.name
                    while dest_path.exists():
                        name_without_ext = Path(original_name).stem
                        extension = Path(original_name).suffix
                        new_name = f"{name_without_ext}_{counter}{extension}"
                        dest_path = target_path / new_name
                        counter += 1
                    
                    shutil.copy2(str(image), str(dest_path))
                
                # Get the copied images for organization
                image_files = get_image_files(str(target_path))
        
        # Organize images into chapters
        organize_images_into_chapters(str(target_path), image_files, images_per_chapter, dry_run)
        
        # Clean up empty directories after organization
        if not dry_run and in_place:
            remove_empty_directories(str(target_path))
        
        print(f"  Completed organizing {manga_title}\n")
    
    print("Organization complete!")
    
    if dry_run:
        print("This was a dry run. Run the script without --dry-run to apply changes.")
    else:
        if in_place:
            print("Original folder structure backed up to '_Backup' directory.")
        else:
            print("Organized manga available in 'Organized_Mihon' directory.")


def show_usage():
    """Display usage information"""
    usage_text = """
Mihon Image Folder Organizer

This script organizes folders containing images into Mihon's local directory structure.
Each folder becomes a manga title with images organized into chapters.

Usage:
    python organize_mihon_images.py [options]

Options:
    -s, --source-path        Source directory containing manga folders (default: current directory)
    -i, --images-per-chapter Number of images per chapter (default: all images in Chapter 1)
    --in-place              Organize folders in-place instead of creating copies
    --dry-run               Preview changes without actually moving files
    -h, --help              Show this help message

Examples:
    python organize_mihon_images.py
    python organize_mihon_images.py --images-per-chapter 15
    python organize_mihon_images.py --images-per-chapter 20
    python organize_mihon_images.py --in-place
    python organize_mihon_images.py --dry-run

Output structure:
    Manga Title/
    ├── Chapter 001/
    │   ├── image1.jpg
    │   ├── image2.jpg
    │   └── ...
    ├── Chapter 002/
    │   ├── image21.jpg
    │   ├── image22.jpg
    │   └── ...
    └── ...

Notes:
    - Images are sorted alphabetically before being organized into chapters
    - All image formats are supported (jpg, png, gif, bmp, webp, tiff)
    - Original folder structure is backed up when using --in-place
    - Without --in-place, organized folders are created in 'Organized_Mihon' directory
"""
    print(usage_text)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Organize image folders for Mihon manga reader')
    parser.add_argument('-s', '--source-path', default=os.getcwd(),
                       help='Source directory containing manga folders (default: current directory)')
    parser.add_argument('-i', '--images-per-chapter', type=int, default=None,
                       help='Number of images per chapter (default: all images in Chapter 1)')
    parser.add_argument('--in-place', action='store_true',
                       help='Organize folders in-place instead of creating copies')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without actually moving files')
    parser.add_argument('--usage', action='store_true',
                       help='Show detailed usage information')
    
    args = parser.parse_args()
    
    if args.usage:
        show_usage()
        return
    
    # Validate source path
    if not os.path.exists(args.source_path):
        print(f"Error: Source path '{args.source_path}' does not exist.")
        sys.exit(1)
    
    # Validate images per chapter
    if args.images_per_chapter is not None and args.images_per_chapter < 1:
        print("Error: images-per-chapter must be greater than 0.")
        sys.exit(1)
    
    # Run the organization
    organize_mihon_image_folders(args.source_path, args.images_per_chapter, 
                               args.dry_run, args.in_place)


if __name__ == "__main__":
    main()
