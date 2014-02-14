import math

def rads (number):
    numdegs = (math.pi * number) / (180)
    return numdegs

def get_hss(filename):
    collins_hss = open(filename)
    data = collins_hss.readlines()
    newdata = []
    for i in data:
        fragmentset = i.strip('\n')
        segments = fragmentset.split('\t')
        newdata.append(segments)
    return newdata

def get_hss_dict(filename):
    collins_hss = get_hss(filename)
    hss_dict = {}
    for i in collins_hss:
        hss_dict[i[0]] = i
    return hss_dict



def calculate_min_i(fos, force, length, E):
    top = fos * force * length * length
    bottom = math.pi * math.pi * E
    min_i = top / bottom
    return min_i

def calculate_min_a(fos, maxstress, force):
    return ((fos * force)/maxstress)

def calculate_min_r(length):
    return (length / 200)

def calculate_hss_needed(member_forces, filename, automatic): #Member forces is the dict from the calculate_member_forces function.
    member_names = member_forces.keys()
    hss_list = get_hss(filename)
    hss_dict = get_hss_dict(filename)
    list_of_members = {}
    for i in member_names:
        currentmem = member_forces[i]
        area = abs(calculate_min_a(2, 350, currentmem[2]))
        if member_forces[i][2] < 0:
            momentofi = abs(calculate_min_i(2, currentmem[2], currentmem[1], 200000))

        else:
            momentofi = 0
        radofg = abs(calculate_min_r(currentmem[1]))
        hssarea = 0
        hssi = 0
        hssr = 0
        counter = 0
        if automatic:
            while  ((hssarea <= area) or (hssi <= momentofi) or (hssr <= radofg)):
                hss = hss_list[counter]
                hssarea = float(hss[2])
                hssi = float(hss[3])
                hssr = float(hss[4])
                counter += 1

        else:
            while not ((hssarea >= area) or (hssi >= momentofi) or (hssr >= radofg)):
                inputname = ''
                while not (inputname in hss_dict.keys()):
                    inputname = raw_input("Enter an HSS name. " + \
                    "\nMinimum area is " + str(area) + \
                    "\nMinimum I is " + str(momentofi) + \
                    "\nMinimum r is " + str(radofg) + '.\n')

                hss = hss_dict[inputname]
                hssarea = float(hss[2])
                hssi = float(hss[3])
                hssr = float(hss[4])
        mass = currentmem[1] * float(hss[1])
        list_of_members[currentmem[0]] = [currentmem[0], currentmem[1], currentmem[2], hss[0], mass]

    return list_of_members

def calculate_deform_mem(member, ym, filename):
    #Divide the actual force acting on the HSS by the area. Next, divide that result - the stress - by
    #the YM times 1000 (to get our strain in mm). Finally, multiply by the length of the member.
    hssdict = get_hss_dict(filename)
    memname = member[0]
    hss = (member[3])
    hssarea = float(hssdict[hss][2])
    memlength = member[1]
    memforce = abs(member[2])
    ym = ym / 1000

    stress = memforce / hssarea
    strain = stress / ym
    deform = strain * memlength
    return deform


def calculate_deflection(listofhss): #We plug in the dict of members with their associated HSS.
#Get the deformation of each member, then use the method of virtual work to get a dummy load on each member. Then,
#multiply deformation by the dummy load and sum them all.
    newmemdict = {}
    for mem in listofhss.keys():
        theentry = listofhss[mem]

        deform = calculate_deform_mem(theentry, 200000, 'collins_corporation_hss_final_sorted.txt')
        theentry.append(deform)
        newmemdict[mem] = theentry



    #Below: equations for finding internal work

    fg = 0.5/math.cos(rads(30)) #Let's get the web members out of the way. For warren all have same loading.

    ef = fg
    de = ef
    cd = de
    bc = cd
    ab = bc



    ac = fg * math.cos(rads(60))
    ce = 2*(fg * math.cos(rads(60))) - ac
    eg = 2*(fg * math.cos(rads(60))) - ce


    bd = 2*(fg*math.cos(rads(60)))
    df = 2*(fg*math.cos(rads(60))) + bd
    fh = 2*(fg*math.cos(rads(60))) + df #Remember to divide fh length by 2 as we're only considering half of the bridge.


    gi = eg
    gh = fg
    hi = gh
    ij = de
    jk = cd
    kl = bc
    lm = ab
    hj = df
    jl = bd
    ik = ce
    km = ac

    #List format: Member name, length, force (negative for compresssion)
    ab = ['ab', 4.16, ab]
    ac = ['ac', 4.16, ac]
    bc = ['bc', 4.16, bc]
    bd = ['bd', 4.16, bd]
    cd = ['cd', 4.16, cd]
    ce = ['ce', 4.16, ce]
    de = ['de', 4.16, de]
    df = ['df', 4.16, df]

    ef = ['ef', 4.16, ef]
    eg = ['eg', 4.16, eg]

    fh = ['fh', 4.16/2, fh]

    fg = ['fg', 4.16, fg]

    dummydict = {}
    the_list = [ab, ac, bc, bd, cd, ce, de, df, ef, eg, fh, fg]

    for i in the_list:
        dummydict[i[0]] = i

#For every element in the dummydict, we go through the matching memdict entry and multiply deform by dummyforce.
    for i in dummydict.keys():
        dummyforce = dummydict[i][2]
        dummydict[i][2] = dummyforce * newmemdict[i][5]

    #Now, sum all of the work values.
    sum_deflxn = 0
    for i in dummydict.keys():
        sum_deflxn += dummydict[i][2]

    return sum_deflxn

def calculate_top_min_windbracing(gravmemdict):
#Whether or not this is necessary depends on your TA.
    #Will program it just in case. Based on the areas of the top HSS's.
    #In our case, the TA instructed us to consider the wind truss and gravity truss as
    #being independent.
    #To distinguish from others, imma use hebrew letters for the top nodes.
    topmembers = []
    for i in gravmemdict.keys():
        if gravmemdict[i][3] == 'Top':
            topmembers.append(gravmemdict[i])

    #Use the maximum force to calculate the minimum resistive force capability of the members.
    #This will be for all vertical members. KEEP IT SIMPLE, STUPID!!

    names = ['aleph-bet', 'gimel-dalet', 'he-vav', 'zayin-heth', 'teth-yod', 'kaph-lamed', 'mem-nun', 'samekh-ayin', 'pe-sadhe', 'qoph-resh', 'shin-tav']


    pass

def calculate_bottom_min_windbracing(railingheight, forceperarea, bridgelength, resistingnodenum):
#Assume that the wind forces the lower truss must resist are equal to the wind force acting on railing.
    #Again, user inputs a truss geometry, and the software will calculate it.
    #Sadly, the hardest part about this is coming up with the geometry, the programming is fairly trivial.
    #Do this before calculating minimum HSS needed.

    #Take the grav members. Imma use greek letters for the bottom nodes.



    area = railingheight * bridgelength
    totforce = area * forceperarea
    loadpernode = totforce / resistingnodenum
    resist = totforce / 2

    ratio1 = math.cos(rads(43.8))
    ratio2 = math.cos(rads(46.2))


    ab = resist
    bd = 0
    ad = (ab - loadpernode) / ratio2
    ac = ad * ratio1
    cd = ad * ratio2
    cf = (cd - loadpernode) / ratio2
    ce = ac + (cf * ratio1)
    df = (ad * ratio1) + bd
    ef = cf * ratio2
    eh = (ef - loadpernode) / ratio2
    fh = (cf * ratio1) + df
    eg = ce + (eh * ratio1)
    gh = eh * ratio2
    gi = df
    hj = fh
    gj = cf
    il = ad
    jl = ac
    ik = bd
    ij = (gj * ratio2)
    kl = resist - (il * ratio2)

    ac = ['ac', 4.16, ac]
    ce = ['ce', 4.16, ce]
    eg = ['eg', 4.16, eg]
    gi = ['gi', 4.16, gi]
    ik = ['ik', 4.16, ik]
    bd = ['bd', 4.16, bd]
    df = ['df', 4.16, df]
    fh = ['fh', 4.16, fh]
    hj = ['hj', 4.16, hj]
    jl = ['jl', 4.16, jl]

    #Don't calculate hss for the above.

    ad = ['ad', 5.77, ad]
    cf = ['cf', 5.77, cf]
    eh = ['eh', 5.77, eh]
    gj = ['gj', 5.77, gj]
    il = ['il', 5.77, il]

    ab = ['ab', 4.00, ab]
    cd = ['cd', 4.00, cd]
    ef = ['ef', 4.00, ef]
    gh = ['gh', 4.00, gh]
    ij = ['ij', 4.00, ij]
    kl = ['kl', 4.00, kl]


    big_fat_list = [ac, ce, eg, gi, ik, bd, df, fh, hj, jl, ad, cf, eh, gj, il, ab, cd, ef, gh, ij, kl]



    return big_fat_list

def calculate_member_forces(dead_load_deck, member_load, live_load, number_of_loaded_joints_excluding_rollers_pins, length, width):
    totalloadperarea = dead_load_deck + member_load + live_load
    area = length * (width/2)
    totalload = totalloadperarea * area




    downwardload = totalload/(number_of_loaded_joints_excluding_rollers_pins + 1)

    supportload = (downwardload * number_of_loaded_joints_excluding_rollers_pins)/2

    #It is up to you to define the forces acting on each member in terms of the other members,
    #and to find out whether they are in tension or in compression.
    #I suggest that you do this calculation for each section of the bridge. Each hanger
    #divides the bridge into another section.


    #Program the below yourself.


    ab = supportload / math.cos(rads(30))
    ac = ab * math.cos(rads(60))
    bc = ab
    bd = 2*(ab*math.cos(rads(60)))
    cd = (bc*math.cos(rads(30)) - downwardload)/math.cos(rads(30))
    ce = ((cd*math.cos(rads(60))) + (bc*math.cos(rads(60))) + ac)
    de = cd
    df = 2*(cd*math.cos(rads(60))) + bd

    ef = (de*math.cos(rads(30)) - downwardload)/math.cos(rads(30))
    eg = ((de*math.cos(rads(60))) + (ef*math.cos(rads(60))) + ce)

    fg = ef
    gh = de
    fh = df
    gi = ce
    hi = cd
    ij = bc
    jk = ab
    ik = ac
    hj = bd

    #List format: Member name, length, force (negative for compresssion)
    ab = ['ab', 4.16, ab]
    ac = ['ac', 4.16, ac]
    bc = ['bc', 4.16, bc]
    bd = ['bd', 4.16, bd]
    cd = ['cd', 4.16, cd]
    ce = ['ce', 4.16, ce]
    de = ['de', 4.16, de]
    df = ['df', 4.16, df]

    ef = ['ef', 4.16, ef]
    eg = ['eg', 4.16, eg]

    fh = ['fh', 4.16, fh]

    fg = ['fg', 4.16, fg]

    gi = ['gi', 4.16, gi]
    gh = ['gh', 4.16, gh]
    hi = ['hi', 4.16, hi]
    ij = ['ij', 4.16, ij]
    jk = ['jk', 4.16, jk]

    hj = ['hj', 4.16, hj]

    ik = ['ik', 4.16, ik]


    big_fat_list = [ab, ac, bc, bd, cd, ce, de, df, ef, eg, fh, fg, gi, gh, hi, ij, jk, hj, ik]
    members_in_compression = ['ab', 'bd', 'df', 'fh', 'hj', 'cd', 'ef', 'hi', 'jk']
    top_chord = ['bd', 'df', 'fh', 'hj']
    bottom_chord = ['ac', 'ce', 'eg', 'gi', 'ik']
    web_members = ['ab','bc','cd','de','ef','fg','gh','hi','ij','jk',]



    big_dict = {}
    for i in big_fat_list:
        big_dict[i[0]] = i




    for i in members_in_compression:
        big_dict[i][2] = -big_dict[i][2]
    for i in top_chord:
        currentmem = big_dict[i]
        currentmem.append('Top')
        big_dict[i] = currentmem
    for i in bottom_chord:
        currentmem = big_dict[i]
        currentmem.append('Bottom')
        big_dict[i] = currentmem
    for i in web_members:
        currentmem = big_dict[i]
        currentmem.append('Web')
        big_dict[i] = currentmem

    return big_dict


print calculate_member_forces(2.5, 0.7, 4.8, 4, 25, 4)
hss = calculate_hss_needed((calculate_member_forces(2500, 700, 4800, 4, 25, 4)), 'collins_corporation_hss_final_sorted.txt', True)
#print (calculate_deflection(calculate_hss_needed((calculate_member_forces(2500, 700, 4800, 5, 25, 4)), 'collins_corporation_hss_final_sorted.txt', True)))

hss_total_weight = 0
for i in hss.keys():
    print "The lightest HSS that " + hss[i][0] + " can use safely is " + hss[i][3]
    hss_total_weight += hss[i][4]

print hss_total_weight
