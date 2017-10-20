The `master` branch of this repository contains [the pulling script](pull.py) and associated documentation.
The extracted data is in the `gh-pages` branch.
To contribute to this project, clone it:

    $ git clone https://github.com/wking/fsf-api.git

And clone another directory to hold `gh-pages`:

    $ cd fsf-api
    $ git clone -b gh-pages https://github.com/wking/fsf-api.git data

After committing a change to `pull.py` in `fsf-api`, change into the data directory, rebuild, and publish:

    $ cd data
    $ make commit
    $ git push origin gh-pages
