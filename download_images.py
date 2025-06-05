import os
import requests
from pathlib import Path

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download: {url}")

def main():
    # Create directories if they don't exist
    base_dir = Path("app/static/images")
    categories_dir = base_dir / "categories"
    base_dir.mkdir(parents=True, exist_ok=True)
    categories_dir.mkdir(parents=True, exist_ok=True)

    # Image URLs and save paths
    images = {
        # Hero image
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09": 
            base_dir / "hero-image.jpg",
        
        # About image
        "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b": 
            base_dir / "about-image.jpg",
        
        # Category images
        "https://images.unsplash.com/photo-1604719312566-8912e9227c6a": 
            categories_dir / "eco-finds.jpg",
        
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09": 
            categories_dir / "eco-friendly.jpg",
        
        "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b": 
            categories_dir / "recycled.jpg",
        
        "https://images.unsplash.com/photo-1604719312566-8912e9227c6a": 
            categories_dir / "water-saving.jpg"
    }

    # Download all images
    for url, save_path in images.items():
        download_image(url, save_path)

if __name__ == "__main__":
    main() 