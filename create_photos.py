import os

os.makedirs('static/uploads', exist_ok=True)

# Create 4 tiny PNGs with single-color data
# Using minimal 1x1 PNG data and adding different colors by altering palette is hard,
# so we just write same tiny PNG (placeholder) for each name but unique file names.

image_bytes = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    b'\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x03\xe2'
    b'\x00\x00\x00\x00IEND\xaeB`\x82'
)
for name in ['alice.png','bob.png','charlie.png','diana.png','default.png']:
    with open(os.path.join('static/uploads', name), 'wb') as f:
        f.write(image_bytes)
print('Created sample user images.')