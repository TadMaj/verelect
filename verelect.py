import sys
import elements
import rows
import ocr
def run_all():
    elements.form_element_model()
    rows.data_row_model()
    ocr.ocr()

def main():
    # Get all arguments
    args = sys.argv[1:]
    
    if len(args) == 0:
        run_all()
        return

    for arg in args:
        match arg:
            case "element":
                elements.form_element_model()
            case "row":
                rows.data_row_model()
            case "ocr":
                ocr.ocr()
            case _:
                print(f"Invalid argument: {arg}")

if __name__ == "__main__":
    main()
