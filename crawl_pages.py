#!/usr/local/Cellar/python/2.7.2/bin/python
from BeautifulSoup import BeautifulSoup
import urllib2, os, csv


def get_district_pages(index_url):
    """
    Takes a URL string and returns a list of tuples with page ID's and district
    names from the 'LEA' drop-down menu.
    """
    index_page = urllib2.urlopen(index_url).read()
    soup = BeautifulSoup(index_page)

    drop_down = soup.find(attrs={'id':'LEA'})

    school_districts = []
    for district in drop_down.findAll('option'):
        if district.text.strip() != "" and district['value'].strip() != "":
            school_districts.append(
                (str((district['value'])), str(district.text.lower()))
            )

    return school_districts

def build_url(district_tuple):
    """
    This is a helper function to build the URL for a district. If URL
    patterns change, we can simply modify this one function.
    """
    return 'http://www.sde.idaho.gov/ReportCard/Index/2009/%s' % district_tuple[0]

def cache_page(district, cache_dir):
    """
    Takes the given district tuple and saves a copy of the source code locally.

    This way we don't have to wait for pages to load and don't bother the website
    with requests.
    """
    url = build_url(district)

    if not cache_dir in os.listdir('.'):
        os.mkdir(cache_dir)

    source = urllib2.urlopen(url).read()

    dest_file = os.path.join(cache_dir, "%s_%s.html" % district)
    open(dest_file, 'wb').write(source)


def scrape_teacher_quality(district, cache_dir=None):
    """
    Takes a district id and name as a tuple and scrapes the relevent page.
    """

    # load data, either from web or cached directory
    if cache_dir is None:
        url = build_url(district)
        try:
            soup = BeautifulSoup(urllib2.urlopen(url).read())
        except:
            print "error loading url:", url
            return
    else:
        try:
            file_in = os.path.join(cache_dir, '%s_%s.html' % district)
            soup = BeautifulSoup(open(file_in, 'r').read())
        except:
            print "file not found:", file_in
            return

    quality_div = soup.find('div', attrs={'id': 'TeacherQuality'})

    header = ['district_id', 'district_name']
    data = list(district)

    for i, table in enumerate(quality_div.findAll('table')):
        header_prefix = 'table%s ' % i

        header_cells = table.findAll('th')
        data_cells = table.findAll('td')

        # some rows have an extra 'th' cell. If so, we need to skip it.
        if len(header_cells) == len(data_cells) + 1:
            header_cells = header_cells[1:]

        header.extend([header_prefix + th.text.strip() for th in header_cells])
        data.extend([td.text.strip() for td in data_cells])

    return {
        'header': header,
        'data': data
    }


def main():
    """
    Main funtion for crawling the data.
    """
    district_pages = get_district_pages('http://www.sde.idaho.gov/reportcard')

    errorlog = open('errors.log', 'wb')
    for district in district_pages:
        print district
        try:
            cache_page(district, 'data')
        except:
            url = build_url(district)
            errorlog.write('Error loading page %s\n' % url)
            continue

    fout = csv.writer(open('parsed_data.csv', 'wb'))

    # write the header
    header = [
        'district_id',
        'district_name',
        'ba_degree',
        'ba_plus_12',
        'ba_plus_24',
        'ma_degree',
        'ma_plus_12',
        'ma_plus_24',
        'phd_degree',
        'degree_total',
        'emergency_cert',
        'poverty_high',
        'poverty_low',
        'poverty_total',
    ]
    fout.writerow(header)

    for district in district_pages:
        parsed_dict = scrape_teacher_quality(district, cache_dir='data')
        if parsed_dict is not None:
            fout.writerow(parsed_dict['data'])
        else:
            errorlog.write('Error parsing district %s (%s)\n' % district)

    del(fout)
    del(errorlog)

if __name__ == "__main__":
    main()
