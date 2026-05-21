from PIL import Image, ImageDraw

def create_coin_stack_image(output_path):
    # Dimensions
    width, height = 1920, 1080
    
    # Colors
    bg_color = (26, 39, 68)      # Dark navy blue (#1a2744)
    gold_color = (201, 168, 76)  # Muted gold (#C9A84C)
    gold_highlight = (230, 200, 120) # Brighter gold for top surface
    gold_shadow = (160, 130, 50)   # Darker gold for sides
    cream_beige = (245, 240, 232) # Warm cream beige (#F5F0E8)
    
    # Create image
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a "floor" or horizon line (Cream Beige accent)
    draw.rectangle([0, height * 0.8, width, height], fill=cream_beige)
    
    # Center position for the coin stack
    cx, cy = width // 2, height // 2 + 100
    coin_width = 300
    coin_height = 60
    stack_height = 8
    
    # Draw stack of coins from bottom to top
    for i in range(stack_height):
        offset_y = i * 25
        # Side of the coin (3D effect)
        draw.ellipse([cx - coin_width//2, cy - offset_y - coin_height//2, 
                      cx + coin_width//2, cy - offset_y + coin_height//2], 
                     fill=gold_shadow)
        
        # Rectangle for the side body
        draw.rectangle([cx - coin_width//2, cy - offset_y - 20, 
                        cx + coin_width//2, cy - offset_y], 
                       fill=gold_shadow)
        
        # Top surface of the coin
        draw.ellipse([cx - coin_width//2, cy - offset_y - 20 - coin_height//2, 
                      cx + coin_width//2, cy - offset_y - 20 + coin_height//2], 
                     fill=gold_color if i < stack_height - 1 else gold_highlight)
        
        # Optional: subtle rim highlight on the top coin
        if i == stack_height - 1:
            draw.ellipse([cx - coin_width//2 + 5, cy - offset_y - 20 - coin_height//2 + 5, 
                          cx + coin_width//2 - 5, cy - offset_y - 20 + coin_height//2 - 5], 
                         outline=(255, 255, 255, 100), width=2)

    # Save the image
    img.save(output_path)
    print(f"Successfully generated image at {output_path}")

if __name__ == "__main__":
    import os
    target_path = r"C:\Programing\PersonalAI\Claude-desktop\bestClip\output\images\test_gemini.png"
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    create_coin_stack_image(target_path)
