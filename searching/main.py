from searching.category import categorize_query
from searching.find_pdf import load_pdf, find_pdf


def main():
    query = input("What are you trying to find? ")

    #Try to find the category of the query

    category = categorize_query(query)

    if category == 'pdf':
        pdf = load_pdf()
        result = find_pdf(query, pdf)
        if result:
            filename = result.split('/')[-1]  # Show just the filename
            print(f"Found PDF: {filename}")
            print(f"Full path: {result}")
        else:
            print("No matching PDF found.")


if __name__ == "__main__":
    main()