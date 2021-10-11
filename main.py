from configparser import ConfigParser

from utils.api_utils import get_data_for_sheet
from utils.sheet_utils import get_sheet_html_string, output_sheet


def main():
    config = ConfigParser(allow_no_value=True)
    config.read('config.ini')

    data_for_sheet = get_data_for_sheet(config)
    sheet_html_string = get_sheet_html_string(data_for_sheet)
    output_sheet(sheet_html_string)


if __name__ == '__main__':
    main()
