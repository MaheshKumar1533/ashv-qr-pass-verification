import csv

# Define sample gate pass data
gate_pass_data = [
    ["pass_number", "holder_name", "valid_until", "name", "email", "phone", "id_proof", "event_id"],
    ["GP001", "John Doe", "2025-03-15", "Johnathan Doe", "johndoe@example.com", "9876543210", "Aadhar Card", 1],
    ["GP002", "Jane Smith", "2025-04-10", "", "janesmith@example.com", "9123456789", "Driver's License", 2],
    ["GP003", "Robert Brown", "2025-05-01", "Rob Brown", "robertbrown@example.com", "", "Passport", 1],
    ["GP004", "Emily Davis", "2025-06-20", "Emily D.", "emilyd@example.com", "9988776655", "", 3],
    ["GP005", "Michael Johnson", "2025-07-15", "", "michaelj@example.com", "8877665544", "Voter ID", 2]
]

# Save data to CSV
csv_filename = "gate_passes.csv"
with open(csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(gate_pass_data)

print(f"CSV file '{csv_filename}' created successfully.")
