from market import *
from ice import *

import json

m = MARKET

m.ipo('t1')
m.ipo('t2')
m.buy('t1', 't2', 2000)

save_market(m, 'market.json')

#print(json.dumps(market_to_dict(m), indent=4))
#print(m.get_portfolio('t1'))
#print(20 * '#')
#print(m2.get_portfolio('t1'))