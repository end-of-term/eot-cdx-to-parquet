import fileinput
import orjson as json
import csv
import sys
import ipaddress
import pprint
import io

from os.path import splitext
from urllib.parse import urlparse

import tldextract

fieldnames = [
    'url_surtkey',
    'url',
    'url_host_name',
    'url_host_surt',
    'url_host_canonical',
    'url_host_tld',
    'url_host_2nd_last_part',
    'url_host_3rd_last_part',
    'url_host_4th_last_part',
    'url_host_5th_last_part',
    'url_host_registry_suffix',
    'url_host_registered_domain',
    'url_host_private_suffix',
    'url_host_private_domain',
    'url_host_name_reversed',
    'url_protocol',
    'url_port',
    'url_path',
    'url_query',
    'fetch_time',
    'fetch_status',
    'content_digest',
    'content_mime_type',
    'content_mime_detected',
    'content_charset',
    'content_languages',
    'content_puid',
    'warc_filename',
    'warc_record_offset',
    'warc_record_length',
    'warc_segment',
    'crawl',
    'subset',
    'extension',
]


buffer = io.StringIO()
writer = csv.DictWriter(buffer, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore')
writer.writeheader()

buffer_write = buffer.write
stdout_write = sys.stdout.write
CHUNK_SIZE = 10000

def reverse_hostname(hostname):
    """
    Reverses a hostname (e.g., 'www.google.com' -> 'com.google.www')
    but leaves IPv4/IPv6 addresses untouched.
    """
    if not hostname:
        return None

    if hostname[-1].isalpha:
        parts = hostname.split('.')
        return ".".join(parts[::-1])
    
    # Check if the hostname is a valid IP address
    try:
        ipaddress.ip_address(hostname)
        # If no error is raised, it's an IP; return it as-is
        return hostname
    except ValueError:
        # Not an IP address, proceed with reversing domain parts
        parts = hostname.split('.')
        return ".".join(parts[::-1])


def get_domain_part(parts, index):
    '''
    Returns th enth-last part of a domain.
    index=1 returns the TDL(e.g., 'com')
    index=2 returns the domain name (e.g., 'example')
    '''

    if not parts:
        return '-'

    # Split by dot and reverse: ['com', 'example', 'www']
    #parts = domain.split('.')[::-1]

    # Adjust 1-based index to 0-based index
    adjusted_index = index - 1

    # Return value if index exists, otherwise None
    return parts[adjusted_index] if 0 <= adjusted_index < len(parts) else '-'


def get_ext(surt):
    *_, path = surt.partition(')')
    path, *_ = path.partition('?')
    path, *_ = path.partition('#')
    _, ext = splitext(path)
    return ext[1:]


def get_segment(filename):
    if not filename:
        return '-'
    return filename.split('/')[3]


def get_crawl(filename):
    if not filename:
        return '-'
    return filename.split('/')[1]


def get_surt_hostname(surt):
    return surt.partition(')')[0]


def get_host_canonical(surt_host):
    return '.'.join(reversed(surt_host.strip(',').split(',')))


pub_extract = tldextract.TLDExtract()
priv_extract = tldextract.TLDExtract(include_psl_private_domains=True)

last_domain = ''
tld_extract_dict = {}

for line in fileinput.input():
    row = {}
    line = line.strip()
    surt, timestamp, json_str = line.split(' ', 2)
    
    try:
        #int(timestamp)
        json_data = json.loads(json_str)
        url = json_data.get('url')
        parsed_url = urlparse(url)
    except:
        break
    
    # A bit of a cache as we work with a surt ordered list of URLs.
    hostname = parsed_url.hostname
    if last_domain != hostname:
        tld_extract_pub = pub_extract(url)
        tld_extract_pri = priv_extract(url)
        
        hostname_rev_parts = hostname.split('.')[::-1]
        
        tld_extract_dict['url_host_tld'] = tld_extract_pub.suffix or '-'
        tld_extract_dict['url_host_registry_suffix'] = tld_extract_pub.suffix or '-'
        tld_extract_dict['url_host_registered_domain'] = tld_extract_pub.top_domain_under_public_suffix or '-'
        tld_extract_dict['url_host_private_suffix'] = tld_extract_pri.suffix or '-'
        tld_extract_dict['url_host_private_domain'] = tld_extract_pri.top_domain_under_public_suffix or '-'
        tld_extract_dict['url_host_surt'] = get_surt_hostname(surt) or '-'
        tld_extract_dict['url_host_canonical'] = get_host_canonical(tld_extract_dict['url_host_surt']) or '-'
        tld_extract_dict['url_host_name_reversed'] = reverse_hostname(hostname) or '-'
        tld_extract_dict['url_host_2nd_last_part'] = get_domain_part(hostname_rev_parts, 2)
        tld_extract_dict['url_host_3rd_last_part'] = get_domain_part(hostname_rev_parts, 3)
        tld_extract_dict['url_host_4th_last_part'] = get_domain_part(hostname_rev_parts, 4)
        tld_extract_dict['url_host_5th_last_part'] = get_domain_part(hostname_rev_parts, 5)
        last_domain = hostname
        

    row['url_surtkey'] = surt
    row['url'] = url
    row['url_host_name'] = hostname
    row['url_host_surt'] = tld_extract_dict['url_host_surt']
    row['url_host_canonical'] = tld_extract_dict['url_host_canonical']
    row['url_host_tld'] = tld_extract_dict['url_host_tld']
    row['url_host_2nd_last_part'] = tld_extract_dict['url_host_2nd_last_part']
    row['url_host_3rd_last_part'] = tld_extract_dict['url_host_3rd_last_part']
    row['url_host_4th_last_part'] = tld_extract_dict['url_host_4th_last_part']
    row['url_host_5th_last_part'] = tld_extract_dict['url_host_5th_last_part']
    row['url_host_registry_suffix'] = tld_extract_dict['url_host_registry_suffix']
    row['url_host_registered_domain'] = tld_extract_dict['url_host_registered_domain']
    row['url_host_private_suffix'] = tld_extract_dict['url_host_private_suffix']
    row['url_host_private_domain'] = tld_extract_dict['url_host_private_domain']
    row['url_host_name_reversed'] = tld_extract_dict['url_host_name_reversed']
    row['url_protocol'] = parsed_url.scheme or '-'
    row['url_port'] = '-' if (port := parsed_url.port) is None else str(port)
    row['url_path'] = parsed_url.path or '-'
    row['url_query'] = parsed_url.query or '-'
    row['fetch_time'] = timestamp
    row['fetch_status'] = json_data.get('status', '-')
    row['content_digest'] = json_data.get('digest', '-')
    row['content_mime_type'] = json_data.get('mime', '-')
    row['content_mime_detected'] = json_data.get('mime-detected', '-')
    row['content_charset'] = json_data.get('charset', '-')
    row['content_languages'] = json_data.get('languages', '-')
    row['warc_filename'] = json_data.get('filename', '-')
    row['warc_record_offset'] = json_data.get('offset', '-')
    row['warc_record_length'] = json_data.get('length', '-')
    row['content_puid'] = json_data.get('puid', '-')
    row['warc_segment'] = get_segment(json_data.get('filename', '-'))
    row['crawl'] = get_crawl(json_data.get('filename', '-'))
    row['subset'] = 'warc'
    row['extension'] = get_ext(surt) or '-'

    writer.writerow(row)
    
    if fileinput.lineno() % CHUNK_SIZE == 0:
        stdout_write(buffer.getvalue())
        buffer.seek(0)
        buffer.truncate(0)

remaining_data = buffer.getvalue()
if remaining_data:
    stdout_write(remaining_data)
