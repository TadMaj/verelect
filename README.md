# Verelect

Verelect is a deep learning powered system for helping with verifying the correctness of the official results of the Dutch election

This project was created and submitted in fulfillment of the requirements for
the VU Bachelor of Science degree in Computer Science

The thesis document can be found [here](docs/thesis-verelect-final.pdf)

## Setup

Data can be aquired by using the following [repo](https://github.com/Sjors/verkiezingen-processen-verbaal)

To aquire data to verify you need to download the EML [data](https://data.overheid.nl/community/organization/kiesraad) then use the [EML-to-Sql tool](https://github.com/kiesraad/eml2sql) to convert it to sql. Lastly the sql database needs to be converted to csv using the script in this repository

## Running

Project can be ran with the command

```
python3 verelect.py
```

Module names can be specified to run only those modules without running the rest.

