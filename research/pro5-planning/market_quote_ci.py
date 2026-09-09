"""Sequential own sale under supplied market parameters and starting inventory.

No other seller, buyer or town consumption is assumed during this scenario.
This is conditional pricing, not a forecast of future starting inventory.
"""
import math


def quote_sale(params, inventory, quantity):
    if type(quantity) is not int or quantity<0:raise ValueError('Nonnegative integer quantity required')
    def shape(kind,x,t):
        x=max(0.0,x)
        if kind=='sq':return x*x
        if kind=='sqrt':return math.sqrt(x)
        if kind=='log':return math.log(1+x)
        if kind=='log10':return math.log10(1+x)
        if kind=='hinge' and t>0:
            u=x/t;return u+8*max(0,u-1)**2
        return x
    prices=[]
    for _ in range(quantity):
        below=inventory<params['I0'];side='below' if below else 'above'
        kind=params[side+'_func'];t=params['T'];base=params['base']
        distance=abs(params['I0']-inventory)
        amplitude=params[side+'_target']*base/shape(kind,t,t)
        price=max(1,int(round(base+(1 if below else -1)*amplitude*shape(kind,distance,t))))
        prices.append(price)
        if price>1:inventory+=1
    return dict(receipts=sum(prices),unit_prices=prices,inventory=inventory)
