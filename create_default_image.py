import os

# Ensure uploads directory exists
os.makedirs('static/uploads', exist_ok=True)

# Minimal 1x1 PNG data
png_data = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x03\xe2"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

with open('static/uploads/default.png', 'wb') as f:
    f.write(png_data)

print('Created static/uploads/default.png')
