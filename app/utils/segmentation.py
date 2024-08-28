import os
import csv


def calculate_segment_index(row, index_mapping):
    age_index = index_mapping["Age"][row["Age"]]
    gender_index = index_mapping["Gender"][row["Gender"]]
    industry_index = index_mapping["Industry"][row["Industry"]]
    return (
        age_index * len(index_mapping["Gender"]) * len(index_mapping["Industry"])
        + gender_index * len(index_mapping["Industry"])
        + industry_index
    )


def map_values_to_index(values):
    return {value: i for i, value in enumerate(values)}


def create_subgroups(segments, num_subgroups_per_segment, contacts_per_subgroup):
    for i, segment in enumerate(segments):
        segment_name = f"Segment-{chr(ord('A') + i)}"
        segment_directory = os.path.join("segmented_contacts", segment_name)
        os.makedirs(segment_directory, exist_ok=True)

        for j in range(num_subgroups_per_segment):
            subgroup_name = f"Group-{j+1}"
            subgroup_contacts = segment[
                j * contacts_per_subgroup : (j + 1) * contacts_per_subgroup
            ]
            subgroup_csv_path = os.path.join(
                segment_directory, f"{segment_name}_Subgroup-{subgroup_name}.csv"
            )

            try:
                with open(subgroup_csv_path, mode="w", newline="") as file:
                    fieldnames = [
                        "Name",
                        "Email",
                        "Age",
                        "Gender",
                        "Industry",
                        "Tech Division",
                        "Company",
                        "Company Website",
                    ]
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(subgroup_contacts)
            except (IOError, csv.Error) as e:
                print(f"Failed to write CSV file: {e}")
