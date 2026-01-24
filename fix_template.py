import os

file_path = 'templates/gym/member_list.html'

with open(file_path, 'r') as f:
    content = f.read()

new_content = content.replace('membership_filter==value', 'membership_filter == value')
new_content = new_content.replace("payment_status=='due'", "payment_status == 'due'")
new_content = new_content.replace("payment_status=='upcoming'", "payment_status == 'upcoming'")

if content != new_content:
    print(f"Fixing {file_path}...")
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("Fixed.")
else:
    print("File already correct (or patterns not found).")
