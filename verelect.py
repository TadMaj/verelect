import sys
import elements
import rows
import ocr
import results

def run_all():
    elements.form_element_model()
    rows.data_row_model()
    ocr.ocr()
    results.parse_results()

def main():
    # Get all arguments
    args = sys.argv[1:]
    
    if len(args) == 0:
        run_all()
        return

    if "elements" in args:
        elements.form_element_model()
    if "rows" in args:
        rows.data_row_model()
    if "ocr" in args:
        ocr.ocr()
    if "results" in args:
        results.results()
        
if __name__ == "__main__":
    main()
