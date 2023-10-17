# ImmiAccount Status Checker

> This script provides functionality to check the status of an ImmiAccount (Australian Department of Home Affairs) and sends an email notification if there is a status change.

## Usage

- The script will log in to the ImmiAccount, retrieve the visa status, and compare it with the previous status stored in data_filename.json.
- If there is a change in status, it will save the new data and send an email notification.

## Important Notes

- Make sure to keep your login credentials (`USERNAME` and `PASSWD`) and other sensitive information secure. Use a `.gitignore` file to exclude `private.py` from version control.
- This script interacts with the ImmiAccount and the website it accesses. Any changes in the website's structure or policies may affect the script's functionality.

## How to Use

### Prerequisites

- Ensure you have Python installed on your system.
- Install the required packages using `pip install beautifulsoup4 pytz selenium`

### Running the Script

1. Clone the repository and navigate to the directory containing the script.
2. Create a file named private.py and define the following variables:
    ```python
    USERNAME = 'your_immiaccount_username'
    PASSWD = 'your_immiaccount_password'
    MAIL_HOST = 'your_mail_host'
    SENDER_ADDRESS = 'your_sender_email'
    SENDER_NAME = 'your_sender_name'
    MAIL_PASSWORD = 'your_mail_password'
    RECEIVER = 'recipient_email'
    ```
    and execute the script using the command `python immiaccount_checker.py`
3. Or directly execute the script using the command:
    ```bash
    python immiaccount_checker.py \
        --username your_username \
        --password your_password \
        --path path_to_save_data \
        --file data_filename.json \
        --mail_host mail_host \
        --sender_address sender_email \
        --sender_name sender_name \
        --mail_password mail_password \
        --mail_to recipient_email
    ```

## Disclaimer

This project is open-source and distributed under the terms of the MIT License. See the [LICENSE](./LICENSE) file for details. The authors provide this software "as-is," without any warranties or guarantees. Use it at your own risk. The authors are not responsible for any misuse or damages caused by this project.
