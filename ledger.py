def calc_dues():
    ps = {"Justin","Mike","Mia"}
    db = [
        ["groceries","Justin",["Mia"],12],
        ["energy","Mia",[],30],
        ["veg","Mike",[],15]
    ]
    dues = {p: {z: 0 for z in ps-{p}} for p in ps}
    for _,by,split,price in db:
        if split:
            split_price = price/(len(split)+1)
            s = split
        else:
            split_price = price/len(ps)
            s = ps-{by}
        for z in s:
            dues[z][by] += split_price
            m = min(dues[z][by], dues[by][z])
            dues[z][by] -= m
            dues[by][z] -= m

    for k,v in dues.items():
        print("%s: %s" % (k, ", ".join("%s-%d" % (z,s) for z,s in v.items())))

calc_dues()