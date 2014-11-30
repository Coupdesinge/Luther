from bs4 import BeautifulSoup
import urllib2
import re
import dateutil.parser
import csv

class Scraper(object):
		
		def connect(self, url):
			page = urllib2.urlopen(url)
			soup = BeautifulSoup(page, 'html5lib')

			return soup

class TypeChanges(object):

		def to_date(self, datestring):
			try:
				date = dateutil.parser.parse(datestring)

				return date
			except TypeError:
				return None

		def money_to_int(self, moneystring):
				try:
						if moneystring is not None:
								return int(moneystring.replace('$', '').replace(',', ''))
						else:
								return None
				except ValueError:
						
						return None

		def budget_to_int(self, budgetstring):
				try:
						budget = budgetstring.split()[0].replace('$', '')
						if '.' in budget:
								budget = budget.split('.')[0] + '500000'
						else:
								budget = budget + '000000'
			
						return int(budget)

				except ValueError:
						return None

class GetDomesticData(Scraper, TypeChanges):

		def get_movie_title(self, soup):
				
			return str(soup.find('title').text).split('(')[0]

		def get_movie_gross(self, soup):
			obj = soup.find(text=re.compile('Domestic Total Gross'))
			if not obj:
				return None
			else:
				return self.money_to_int(obj.findNextSibling().text)

		def get_movie_distributor(self, soup):
				
			obj = soup.find(text=re.compile('Distributor'))
			if not obj:
				return None
			else:
				return str((obj.next_sibling())[0].text)

		#def get_movie_rating(self)

		def get_movie_release_date(self, soup):

			obj = soup.find(text=re.compile('Release Date'))
			if not obj:
				return None
			else: 
				return self.to_date(obj.next_sibling.text)

		def get_movie_budget(self, soup):

			obj = soup.find(text=re.compile('Production Budget'))
			if not obj:
				return None
			else:
				return self.budget_to_int(obj.next_sibling.text)

		def get_movie_genre(self, soup):

			genre_list = []
			for link in soup.find_all('a'):
				if link['href'].startswith('/genres/chart/'):
					genre_list.append(str(link.text))
			return genre_list

		
class GetForeignData(Scraper, TypeChanges):
	
		def open_foreign_data_page(self, soup, check='False'):
			
			link_list = []
			base_url = 'http://boxofficemojo.com'
			for link in soup.find_all('a'):
				if link['href'].startswith('/movies/?page=intl'):
					link_list.append(link)

			if check == 'True':
				try:
					link = link_list[1]
					return self.money_to_int(link.find_parent('td').findNextSibling().text)

				except IndexError:
					return None
			else:
				try:
					foreign_url = base_url + str(link_list[0]['href'])
					foreign_page = urllib2.urlopen(foreign_url)
					foreign_soup = BeautifulSoup(foreign_page)

					return foreign_soup
				except IndexError:
					return None

		def get_movie_foreign_gross(self, soup):
				
			return self.open_foreign_data_page(soup, 'True')
		
		def make_dict(self, soup):
			foreign_data_dict = {}
			try:
				for link in soup.find_all('a'):
					if link['href'].startswith('/movies/?page=intl&country'):
						section = link.find_parent('tr')
						foreign_data_dict[str(section.contents[0].get_text())] = [str(section.contents[2].get_text()), 
						self.to_date(section.contents[4].get_text()), self.money_to_int(section.contents[10].get_text())]
				del foreign_data_dict['FOREIGN TOTAL']
				return foreign_data_dict
			except (IndexError, AttributeError) as e:
				return foreign_data_dict

		def get_foreign_data(self, soup):
			"""opens foreign data link on movie page and gathers foreign gross data"""

			new_soup = self.open_foreign_data_page(soup)
			foreign_data_dict = self.make_dict(new_soup)
			
			return foreign_data_dict

class MovieData(GetDomesticData, GetForeignData):

		base_url = 'http://www.boxofficemojo.com' 
		
		def url_to_url_list(self, page_url):
			"""input top grossing of year ___ url from boxofficemojo
			output a list of movie links"""
			url_list = []
			soup = self.connect(page_url)
			print page_url
			for link in soup.find_all('a'):
					try:
							if link['href'].startswith('/movies/?id'):
								url_list.append(self.base_url + str(link['href']))
					except KeyError:
							pass
			
			return url_list

		def return_movie_features(self, soup):
			feature_list = []
			feature_list.append(self.get_movie_title(soup))
			feature_list.append(self.get_movie_gross(soup))
			feature_list.append(self.get_movie_foreign_gross(soup))
			feature_list.append(self.get_movie_distributor(soup))
			feature_list.append(self.get_movie_release_date(soup))
			feature_list.append(self.get_movie_budget(soup))
			#feature_list.append(self.get_movie_director(soup))
			feature_list.append(self.get_movie_genre(soup))
			feature_list.append(self.get_foreign_data(soup))
		    	
			return feature_list
				
		def return_full_list(self, page_url):

			with open('moviedata2013.csv', 'w') as csvfile:
				csvwriter = csv.writer(csvfile)
				movie_url_list = self.url_to_url_list(page_url)
				
				i = 0
				for elem in movie_url_list:
					soup = self.connect(elem)
					full_list = self.return_movie_features(soup)
					csvwriter.writerow(full_list)
					print 'row %i written' % i
					i += 1
				print 'success'


if __name__ == '__main__':
    #url = 'http://www.boxofficemojo.com/yearly/chart/?page=1&view=releasedate&view2=domestic&yr=2009&p=.htm'
	#url = 'http://www.boxofficemojo.com/yearly/chart/?yr=2010&p=.htm'
	#url = 'http://www.boxofficemojo.com/yearly/chart/?yr=2011&p=.htm'
	#url = 'http://www.boxofficemojo.com/yearly/chart/?yr=2012&p=.htm'
	url = 'http://www.boxofficemojo.com/yearly/chart/?yr=2013&p=.htm'
	test = MovieData()
	test.return_full_list(url)
	
