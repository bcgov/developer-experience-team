import os
import sys
import yaml

def get_front_matter(file_path):
    with open(file_path, 'r') as file:
        front_matter = {}
        lines = file.readlines()

        if lines[0].strip() == '---':
            front_matter_lines = []
            for line in lines[1:]:
                if line.strip() == '---':
                    break
                front_matter_lines.append(line)

            front_matter = yaml.safe_load(''.join(front_matter_lines))

        return front_matter

def generate_nav_entries(root_path, mkdocs_file_path):
    nav_entries = []
    for root, dirs, files in os.walk(root_path):
        if root == root_path:
            # Skip the root directory itself, just process its subdirectories
            continue
        sub_heading = os.path.basename(root).replace('-', ' ').capitalize()

        nav_entry = {'{}'.format(sub_heading): []}

        for file_name in files:
            if file_name.endswith('.md'):
                file_path = os.path.join(root, file_name)
                front_matter = get_front_matter(file_path)
                if 'title' in front_matter:
                    nav_entry['{}'.format(sub_heading)].append(
                        {front_matter['title']: os.path.join(mkdocs_file_path, file_name)})
                    
        if nav_entry['{}'.format(sub_heading)]:
            nav_entries.append(nav_entry)

    return nav_entries

def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data"""
    if data.count('\n') > 0:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def generate_mkdocs_yml(root_path, mkdocs_file_path, output_file='mkdocs.yml'):
    nav_entries = generate_nav_entries(root_path, mkdocs_file_path)
    mkdocs_nav = {'nav': nav_entries}
    mkdocs_intro = {
        'site_name':'BC Government Private Cloud Technical Documentation',
        'docs_dir':'src'   
    }

    mkdocs_end = { 
        'plugins': ['techdocs-core'],
        'exclude_docs': 'drafts/\ncomponents/\nhooks/\npages/\nutils/\n'
    }

    with open(output_file, 'w') as file:                 
        yaml.add_representer(str, str_presenter)
        yaml.dump(mkdocs_intro, file, sort_keys=False)
        yaml.dump(mkdocs_nav, file, sort_keys=False)
        yaml.dump(mkdocs_end, file, sort_keys=False)
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mkdocs.py directory_path [mkdocs_file_path]")
        sys.exit(1)

    directory_path = sys.argv[1]
    file_path = ''
    if len(sys.argv) > 2:
        file_path = sys.argv[2]
    generate_mkdocs_yml(directory_path, file_path)
