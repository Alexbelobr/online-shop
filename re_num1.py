import re

text = 'abcdfghjk'

parser = re.search('a[b-f]*f', text)
print(parser.group())