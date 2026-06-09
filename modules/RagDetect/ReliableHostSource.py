reliable_sources = [
    # Original Nigerian News Sites
    "punchng.com", "vanguardngr.com", "guardian.ng", "premiumtimesng.com",
    "dailypost.ng", "thenationonlineng.net", "saharareporters.com", "channelstv.com",
    "naijanews.com", "tribuneonlineng.com", "pmnewsnigeria.com", "sunnewsonline.com",
    "leadership.ng", "tvcnews.tv", "thisdaylive.com", "businessday.ng",
    "dailytrust.com", "blueprint.ng", "thecable.ng", "ripplesnigeria.com",
    "newtelegraphng.com", "nigerianbulletin.com", "informationng.com", "ynaija.com",
    "bellanaija.com", "notjustok.com", "naijaloaded.com.ng", "tooxclusive.com",
    "lindaikejisblog.com", "that1960chick.com", "pulse.ng", "olorisupergal.com",
    "fameloaded.com", "nairaland.com",

    # Original International News
    "bbc.com", "cnn.com", "aljazeera.com", "reuters.com", "apnews.com",
    "theguardian.com", "nytimes.com", "washingtonpost.com", "bloomberg.com",
    "forbes.com", "cnbc.com", "ft.com", "npr.org", "abcnews.go.com",
    "nbcnews.com", "latimes.com", "economist.com", "dw.com", "cbc.ca",

    # Global Entertainment & Culture
    "eonline.com", "tmz.com", "billboard.com", "variety.com", "hollywoodreporter.com",
    "buzzfeed.com", "people.com", "complex.com", "rollingstone.com", "pitchfork.com",
    "vanityfair.com", "vulture.com", "etonline.com", "mtv.com", "vh1.com",

    # Global Sports
    "espn.com", "skysports.com", "goal.com", "bleacherreport.com",
    "eurosport.com", "cbssports.com", "foxsports.com", "nba.com",
    "fifa.com", "uefa.com", "mlssoccer.com", "sportingnews.com",

    # Nigerian Sports & Entertainment
    "brila.net", "npfl.ng", "complete-sports.com", "allnigeriasoccer.com",

    # African & Pan-African News
    "africanews.com", "mg.co.za", "citinewsroom.com", "theeastafrican.co.ke",
    "ghanaweb.com", "nation.africa", "dailynation.africa", "standardmedia.co.ke",
    "enca.com", "sabcnews.com", "herald.ng", "zambianobserver.com",

    # Tech, Business & Startup News
    "techpoint.africa", "techcabal.com", "technext24.com", "benjamindada.com",
    "disrupt-africa.com", "venturesafrica.com", "crunchbase.com", "techcrunch.com",
    "theverge.com", "wired.com", "mashable.com", "thenextweb.com", "hbr.org",

    # Finance & Economy
    "cointelegraph.com", "coindesk.com", "investopedia.com", "yahoo.com/finance",
    "marketwatch.com", "nasdaq.com", "barrons.com", "money.cnn.com",

    # Education & Science
    "nature.com", "sciencedaily.com", "nationalgeographic.com", "newscientist.com",

    # Fact-Checking & Research
    "snopes.com", "factcheck.org", "politifact.com", "fullfact.org",

    # ADDITIONAL 500 SOURCES BY REGION AND CATEGORY:

    # NORTH AMERICA
    # USA - News & Politics (65)
    "axios.com", "fivethirtyeight.com", "thehill.com", "realclearpolitics.com", "thedailybeast.com",
    "reason.com", "motherjones.com", "theintercept.com", "propublica.org", "rollcall.com",
    "theatlantic.com", "newyorker.com", "harpers.org", "foreignpolicy.com", "foreignaffairs.com",
    "chicagotribune.com", "bostonglobe.com", "denverpost.com", "sfchronicle.com", "dallasnews.com",
    "seattletimes.com", "miamiherald.com", "ajc.com", "startribune.com", "azcentral.com",
    "detroitnews.com", "freep.com", "orlandosentinel.com", "baltimoresun.com", "mercurynews.com",
    "inquirer.com", "houstonchronicle.com", "courier-journal.com", "dispatch.com", "statesman.com",
    "jsonline.com", "tennessean.com", "indystar.com", "sltrib.com", "newsobserver.com",
    "oregonlive.com", "sacbee.com", "star-telegram.com", "reviewjournal.com", "pilotonline.com",
    "buffalonews.com", "arkansasonline.com", "providencejournal.com", "kansascity.com", "desmoinesregister.com",
    "cincinnati.com", "clarionledger.com", "omaha.com", "courier-journal.com", "oklahoman.com",
    "delawareonline.com", "democratandchronicle.com", "greenvilleonline.com", "knoxnews.com", "commercialappeal.com",

    # Canada (15)
    "nationalpost.com", "theglobeandmail.com", "macleans.ca", "torontostar.com", "montrealgazette.com",
    "vancouversun.com", "ottawacitizen.com", "calgarysun.com", "edmontonsun.com", "winnipegfreepress.com",
    "thestar.com", "lapresse.ca", "ledevoir.com", "journaldemontreal.com", "tvanouvelles.ca",

    # Mexico & Central America (15)
    "eluniversal.com.mx", "milenio.com", "jornada.com.mx", "excelsior.com.mx", "reforma.com",
    "elsalvador.com", "laprensa.hn", "prensalibre.com", "nacion.com", "teletica.com",
    "elsiglo.com.pa", "laprensa.com.ni", "diario.mx", "elnuevodia.com", "periodicocubano.com",

    # Caribbean (10)
    "jamaicaobserver.com", "jamaicagleaner.com", "tribune242.com", "thenassauguardian.com", "nationnews.com",
    "trinidadexpress.com", "newsday.co.tt", "barbadostoday.bb", "dominicavibes.dm", "stluciatimes.com",

    # SOUTH AMERICA (25)
    "folha.uol.com.br", "globo.com", "estadao.com.br", "clarin.com", "lanacion.com.ar",
    "latercera.com", "emol.com", "eltiempo.com", "elespectador.com", "elcomercio.pe",
    "larepublica.pe", "elobservador.com.uy", "elpais.com.uy", "abc.com.py", "ultimahora.com",
    "eldeber.com.bo", "larazon.com", "eluniverso.com", "elcomercio.com", "lahora.com.ec",
    "eltiempo.com.ve", "elnacional.com", "noticias24.com", "ultimasnoticias.com.ve", "elestimulo.com",

    # EUROPE
    # UK & Ireland (20)
    "dailymail.co.uk", "thetimes.co.uk", "thesun.co.uk", "express.co.uk", "standard.co.uk",
    "metro.co.uk", "spectator.co.uk", "newstatesman.com", "channel4.com/news", "itv.com/news",
    "prospectmagazine.co.uk", "theweek.co.uk", "scotsman.com", "heraldscotland.com", "walesonline.co.uk",
    "belfasttelegraph.co.uk", "irishtimes.com", "independent.ie", "rte.ie/news", "thejournal.ie",

    # Germany, Austria & Switzerland (20)
    "spiegel.de", "faz.net", "sueddeutsche.de", "zeit.de", "welt.de",
    "tagesschau.de", "stern.de", "handelsblatt.com", "focus.de", "tagesspiegel.de",
    "nzz.ch", "tagesanzeiger.ch", "blick.ch", "20min.ch", "watson.ch",
    "derstandard.at", "diepresse.com", "kurier.at", "orf.at", "krone.at",

    # France & Francophone Europe (15)
    "lemonde.fr", "lefigaro.fr", "liberation.fr", "leparisien.fr", "20minutes.fr",
    "lexpress.fr", "lepoint.fr", "nouvelobs.com", "ouest-france.fr", "sudouest.fr",
    "rtbf.be", "lesoir.be", "lalibre.be", "letemps.ch", "tio.ch",

    # Italy (10)
    "repubblica.it", "corriere.it", "lastampa.it", "ilsole24ore.com", "ansa.it",
    "rainews.it", "ilfattoquotidiano.it", "ilmessaggero.it", "ilgiornale.it", "adnkronos.com",

    # Spain & Portugal (15)
    "elpais.com", "elmundo.es", "abc.es", "lavanguardia.com", "eldiario.es",
    "elconfidencial.com", "20minutos.es", "publico.es", "larazon.es", "rtve.es",
    "publico.pt", "dn.pt", "expresso.pt", "observador.pt", "jn.pt",

    # Nordics (15)
    "dn.se", "svd.se", "expressen.se", "aftonbladet.se", "svt.se",
    "dr.dk", "politiken.dk", "berlingske.dk", "tv2.dk", "hs.fi",
    "yle.fi", "vg.no", "aftenposten.no", "nrk.no", "bt.no",

    # Eastern Europe (20)
    "gazeta.ru", "kommersant.ru", "rbc.ru", "interfax.ru", "tass.ru",
    "pravda.com.ua", "ukrinform.ua", "kyivpost.com", "unian.info", "wyborcza.pl",
    "onet.pl", "wp.pl", "delfi.lt", "15min.lt", "postimees.ee",
    "24chasa.bg", "novinite.com", "index.hu", "digi24.ro", "hotnews.ro",

    # MIDDLE EAST & NORTH AFRICA (40)
    "haaretz.com", "ynetnews.com", "timesofisrael.com", "jpost.com", "alarabiya.net",
    "middleeasteye.net", "al-monitor.com", "dailysabah.com", "hurriyetdailynews.com",
    "ahram.org.eg", "egyptindependent.com", "madamasr.com", "jordantimes.com", "petra.gov.jo",
    "naharnet.com", "lorientlejour.com", "gulfnews.com", "khaleejtimes.com", "thenational.ae",
    "arabnews.com", "saudigazette.com.sa", "timesofoman.com", "thepeninsulaqatar.com", "qatarday.com",
    "bahraintribune.com", "yenisafak.com", "sabq.org", "masrawy.com", "youm7.com",
    "moroccoworldnews.com", "hespress.com", "leconomiste.com", "allafrica.com/morocco", "libyaherald.com",
    "tunisienumerique.com", "leconomistemaghrebin.com", "letemps.com.tn", "algerie-eco.com", "tsa-algerie.com",

    # SUB-SAHARAN AFRICA (35)
    # West Africa
    "punchng.com", "thecable.ng", "premiumtimesng.com", "myjoyonline.com", "peacefmonline.com",
    "citifmonline.com", "yen.com.gh", "seneweb.com", "dakaractu.com", "senego.com",
    "apanews.net", "guineenews.org", "abidjan.net", "fratmat.info", "aouaga.com",

    # East Africa
    "thecitizen.co.tz", "dailynews.co.tz", "theeastafrican.co.ke", "nation.co.ke", "standardmedia.co.ke",
    "monitor.co.ug", "newvision.co.ug", "newtimes.co.rw", "igihe.com", "ethiopianreporter.com",
    "addisfortune.net", "addisstandard.com", "hiiraan.com", "radiodalsan.com", "shabelle.net",

    # Southern Africa
    "sowetanlive.co.za", "dailymaverick.co.za", "businesslive.co.za", "ewn.co.za", "namibian.com.na",

    # ASIA
    # East Asia (35)
    "scmp.com", "thestandard.com.hk", "hk01.com", "globaltimes.cn", "chinadaily.com.cn",
    "sixthtone.com", "caixin.com", "yicai.com", "thepaper.cn", "japantimes.co.jp",
    "asahi.com", "mainichi.jp", "yomiuri.co.jp", "nhk.or.jp", "kyodonews.net",
    "koreaherald.com", "koreatimes.co.kr", "chosun.com", "joongang.co.kr", "hani.co.kr",
    "taipeitimes.com", "chinapost.nownews.com", "focustaiwan.tw", "udn.com", "ltn.com.tw",
    "thestar.com.my", "nst.com.my", "malaymail.com", "bernama.com", "thejakartapost.com",
    "kompas.com", "detik.com", "tribunnews.com", "thejakartapost.com", "vinanet.vn",

    # South Asia (25)
    "indianexpress.com", "thehindu.com", "hindustantimes.com", "ndtv.com", "news18.com",
    "financialexpress.com", "livemint.com", "telegraphindia.com", "deccanherald.com", "tribuneindia.com",
    "dawn.com", "tribune.com.pk", "geo.tv", "thenews.com.pk", "brecorder.com",
    "dailystar.net", "bdnews24.com", "prothomalo.com", "colombopage.com", "dailymirror.lk",
    "thehimalayantimes.com", "kathmandupost.com", "kuenselonline.com", "bhutantimes.bt", "thebhutanese.bt",

    # Central Asia (10)
    "akipress.com", "kabar.kg", "24.kg", "azernews.az", "trend.az",
    "inform.kz", "kazinform.kz", "astanatimes.com", "uzreport.uz", "uza.uz",

    # OCEANIA (20)
    "theaustralian.com.au", "afr.com", "theage.com.au", "smh.com.au", "news.com.au",
    "9news.com.au", "abc.net.au", "sbs.com.au", "theguardian.com/au", "watoday.com.au",
    "nzherald.co.nz", "stuff.co.nz", "rnz.co.nz", "tvnz.co.nz", "newshub.co.nz",
    "fijitimes.com", "fijivillage.com", "samoanews.com", "pina.com.fj", "pacnews.org",

    # SPECIALIZED MEDIA
    # Technology (25)
    "techcrunch.com", "arstechnica.com", "thenextweb.com", "wired.com", "theverge.com",
    "cnet.com", "zdnet.com", "venturebeat.com", "engadget.com", "gizmodo.com",
    "tomshardware.com", "anandtech.com", "macrumors.com", "androidpolice.com", "xda-developers.com",
    "techradar.com", "pcworld.com", "extremetech.com", "slashdot.org", "bleepingcomputer.com",
    "hackernews.com", "techmeme.com", "technologyreview.com", "hackernoon.com", "9to5mac.com",

    # Business & Finance (25)
    "ft.com", "economist.com", "bloomberg.com", "reuters.com", "wsj.com",
    "cnbc.com", "businessinsider.com", "fortune.com", "moneycontrol.com", "livemint.com",
    "marketwatch.com", "seekingalpha.com", "investing.com", "zacks.com", "thestreet.com",
    "morningstar.com", "cnbctv18.com", "barrons.com", "fool.com", "businessstandard.com",
    "ibtimes.com", "hbr.org", "fastcompany.com", "mckinsey.com", "bain.com",

    # Science & Health (25)
    "scientificamerican.com", "science.org", "nature.com", "newscientist.com", "livescience.com",
    "sciencedaily.com", "medicalnewstoday.com", "webmd.com", "health.com", "healthline.com",
    "mayoclinic.org", "nih.gov", "sciencealert.com", "medicaldaily.com", "sciencefocus.com",
    "sciencenews.org", "popsci.com", "discovermagazine.com", "phys.org", "sciencemag.org",
    "eurekalert.org", "medscape.com", "thelancet.com", "bmj.com", "nejm.org",

    # Sports (25)
    "espn.com", "sports.yahoo.com", "cbssports.com", "nbcsports.com", "foxsports.com",
    "bleacherreport.com", "si.com", "theathletic.com", "sportingnews.com", "sbnation.com",
    "goal.com", "skysports.com", "bbc.com/sport", "eurosport.com", "marca.com",
    "as.com", "lequipe.fr", "kicker.de", "sportbild.de", "sportmediaset.mediaset.it",
    "supersport.com", "sportstarlive.com", "sportal.bg", "gazzetta.gr", "sport24.gr",

    # Entertainment (25)
    "variety.com", "hollywoodreporter.com", "deadline.com", "ew.com", "imdb.com",
    "indiewire.com", "screenrant.com", "cinemablend.com", "avclub.com", "empireonline.com",
    "digitalspy.com", "rottentomatoes.com", "metacritic.com", "polygon.com", "kotaku.com",
    "gamespot.com", "ign.com", "eurogamer.net", "rockpapershotgun.com", "pcgamer.com",
    "nintendolife.com", "pushsquare.com", "playstationlifestyle.net", "vg247.com", "gamasutra.com",

    # Additional International Fact-Checking (15)
    "factcheck.org", "politifact.com", "snopes.com", "truthorfiction.com", "checkyourfact.com",
    "factcheckni.org", "factnameh.com", "faktograf.hr", "verificat.cat", "maldita.es",
    "correctiv.org", "mimikama.at", "teyit.org", "stopfake.org", "ellinikahoaxes.gr",

    # ADDITIONAL CATEGORIES
    # Media Analysis (10)
    "niemanlab.org", "cjr.org", "poynter.org", "mediagazer.com", "mediaite.com",
    "adweek.com", "pressgazette.co.uk", "themediabriefing.com", "mediapost.com", "journalism.co.uk",

    # Regional/Local US Media (10)
    "nj.com", "mlive.com", "masslive.com", "pennlive.com", "cleveland.com",
    "al.com", "oregonlive.com", "silive.com", "syracuse.com", "nola.com",

    # Travel & Lifestyle (10)
    "travelandleisure.com", "cntraveler.com", "afar.com", "lonelyplanet.com", "fodors.com",
    "timeout.com", "eater.com", "bonappetit.com", "epicurious.com", "seriouseats.com",

    # Environmental (10)
    "nationalgeographic.com", "treehugger.com", "grist.org", "ecowatch.com", "ensia.com",
    "earthisland.org", "environmentalhealth.news", "yaleclimateconnections.org", "e360.yale.edu", "insideclimatenews.org"
]
