The [mkdocs.py](mkdocs.py) file was created to generate the mkdocs.yml file for the private cloud techdocs.

It needs more work if to be used in future.

Specifically for private cloud:
* Take sort order into account
* Allow for override of category heading names
  * It currently uses the directory name, but some category headings are slightly different from the name.

If this is a script that will be used for more projects, consider the following:

* Accept config file rather than command line arguments?
* Update script so it is not using private cloud specific name, dir, excluded dirs etc
* Use a templating framework? jnija etc?
  * See helm as inspiration. It creates yml files based on a template and an input values.yaml file. 