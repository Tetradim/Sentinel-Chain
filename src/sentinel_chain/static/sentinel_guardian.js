
(() => {
  "use strict";

  const EDGE_HEATMAP_SAMPLE = {"exported_at":"2026-07-02T12:35:57.698Z","symbol":"SPY","mode":"GEX","current_price":745.7,"support":745.3695,"resistance":746.0305,"level_source":"S/R API","max_pain":745.7,"risk_score":68,"regime":"Range / Neutral","regime_confidence":54.16,"levels":[{"symbol":"SPY","support":745.3695,"price":745.7,"resistance":746.0305,"status":"At resistance","tone":"warn","distancePct":0.04432077242857924,"source":"S/R API"},{"symbol":"QQQ","support":481.5954042596983,"price":489.227350934273,"resistance":495.44053829113824,"status":"In range","tone":"ok","distancePct":1.2699999999999991,"source":"watchlist fallback"},{"symbol":"NVDA","support":146.01997905683464,"price":148.42445523158634,"resistance":150.4133429316896,"status":"In range","tone":"ok","distancePct":1.3400000000000134,"source":"watchlist fallback"},{"symbol":"AAPL","support":209.43212457403004,"price":213.0107044080859,"resistance":216.0141553402399,"status":"In range","tone":"ok","distancePct":1.4099999999999995,"source":"watchlist fallback"},{"symbol":"LNR","support":247.1053837783677,"price":251.4811558908688,"resistance":255.20307699805363,"status":"In range","tone":"ok","distancePct":1.4799999999999929,"source":"watchlist fallback"},{"symbol":"MU","support":283.4539783425854,"price":288.64967244662466,"resistance":293.12374236954736,"status":"In range","tone":"ok","distancePct":1.5500000000000043,"source":"watchlist fallback"},{"symbol":"SNDK","support":318.44357598553904,"price":324.4788832133066,"resistance":329.73544112136216,"status":"In range","tone":"ok","distancePct":1.6200000000000052,"source":"watchlist fallback"},{"symbol":"INTC","support":353.50220780321644,"price":360.42231627571005,"resistance":366.5134534207695,"status":"In range","tone":"ok","distancePct":1.6899999999999897,"source":"watchlist fallback"},{"symbol":"IRDM","support":390.2803160607513,"price":398.16396251862,"resistance":405.17164825894776,"status":"In range","tone":"ok","distancePct":1.7600000000000116,"source":"watchlist fallback"}],"series":[{"time":"09:00","price":739.9269486889135,"allow":34.90520515745148,"risk":59.1724945027374,"volume":162.10181851871312,"heat":88.94415045351526},{"time":"09:03","price":740.2704226790174,"allow":38.045977396473994,"risk":60.84018727945238,"volume":246.0928197298199,"heat":92.42271072661626},{"time":"09:06","price":740.7719901082994,"allow":36.75961032937145,"risk":65.63837211514064,"volume":207.68450462259352,"heat":51.407914561624246},{"time":"09:09","price":740.8927586488214,"allow":34.0434716326106,"risk":60.63038221047145,"volume":301.61357051692903,"heat":66.62810670684809},{"time":"09:12","price":741.218739398479,"allow":36.944056845561335,"risk":61.04452970086847,"volume":222.95940680895,"heat":64.14760970537542},{"time":"09:15","price":741.7728790869977,"allow":41.69656414906469,"risk":65.08905907481997,"volume":220.86847417522222,"heat":18.721833833965427},{"time":"09:18","price":742.1335199870075,"allow":43.494283033972174,"risk":67.74693845488598,"volume":146.58176263794303,"heat":8.170384021789829},{"time":"09:21","price":742.2415655603214,"allow":40.0456249858038,"risk":66.14127963294443,"volume":222.71804814692587,"heat":4.264608753526133},{"time":"09:24","price":742.2963177911497,"allow":43.204397190227255,"risk":67.64220702478235,"volume":225.97988097928464,"heat":2.143529055271742},{"time":"09:27","price":742.6194408982101,"allow":45.51039122707208,"risk":60.92165739128913,"volume":149.28472482599318,"heat":3.538055379878685},{"time":"09:30","price":742.7803355835388,"allow":42.55104798365844,"risk":67.61833138720557,"volume":262.74252062663436,"heat":12.659760482133201},{"time":"09:33","price":742.9587886936207,"allow":50.53460688886658,"risk":68.9377457729642,"volume":149.42471224814653,"heat":26.20388352869658},{"time":"09:36","price":743.2044382825339,"allow":46.13797905795233,"risk":64.07363275966014,"volume":215.4349536402151,"heat":59.388432285505786},{"time":"09:39","price":743.2255321953627,"allow":51.887331503263454,"risk":66.08429087605566,"volume":46.35754476767033,"heat":70.62699384263028},{"time":"09:42","price":743.1293753043587,"allow":48.7038423124991,"risk":69.26127299389731,"volume":208.03509616293013,"heat":69.75534783375132},{"time":"09:45","price":743.2542302527052,"allow":51.47018316546395,"risk":68.41366917016178,"volume":76.69096519704908,"heat":82.58817046123158},{"time":"09:48","price":743.1604715663364,"allow":53.412106266867966,"risk":66.91558830250594,"volume":81.53252999763936,"heat":93.71167916465242},{"time":"09:51","price":743.0359280787073,"allow":51.89408981595256,"risk":67.58996732548775,"volume":66.24354868661612,"heat":77.9584241321081},{"time":"09:54","price":743.0831129741856,"allow":56.4662521020182,"risk":61.99244152072849,"volume":49.812604608014226,"heat":99.91388040682023},{"time":"09:57","price":743.3197225058383,"allow":57.212874718246454,"risk":62.686548178079825,"volume":172.54205731209368,"heat":81.27106905609224},{"time":"09:00","price":743.4804698369194,"allow":56.866232347926974,"risk":57.373702141544115,"volume":160.92704122886062,"heat":51.778254639875406},{"time":"09:03","price":743.5433816797249,"allow":60.88711296546037,"risk":58.53263990479564,"volume":129.42182294093072,"heat":16.327794971102744},{"time":"09:06","price":743.5319362988262,"allow":56.948769789625516,"risk":61.7584536691358,"volume":108.78703586757183,"heat":28.024854401850668},{"time":"09:09","price":743.5590772472048,"allow":62.0386063614901,"risk":58.277990835619626,"volume":75.45618605334312,"heat":0.22603208858801338},{"time":"10:12","price":743.7968046372335,"allow":63.39859449692346,"risk":59.57581869597631,"volume":115.11068250052631,"heat":6.168853519352133},{"time":"10:15","price":744.0148916863168,"allow":62.32612985902046,"risk":60.42335570847767,"volume":53.70136314537376,"heat":23.64542227458256},{"time":"10:18","price":743.8378655734629,"allow":67.22578508937835,"risk":51.89378368175613,"volume":116.44793141633272,"heat":1.76094772217386},{"time":"10:21","price":743.6238438393709,"allow":63.96731242171583,"risk":54.65422201861437,"volume":213.08254049625248,"heat":7.083388600902559},{"time":"10:24","price":743.7255954282427,"allow":69.19793491351473,"risk":49.30306620318377,"volume":102.92341356165707,"heat":0},{"time":"10:27","price":743.6296956028121,"allow":67.61030361548535,"risk":49.49696074433336,"volume":74.50709871482104,"heat":0},{"time":"10:30","price":743.6078516386148,"allow":70.14098334398975,"risk":48.27986187309818,"volume":87.9812483722344,"heat":0},{"time":"10:33","price":743.4857105183473,"allow":68.10754578482604,"risk":47.71498418912237,"volume":169.93786436971277,"heat":3.0843699176270007},{"time":"10:36","price":743.3928132344636,"allow":67.51727484572545,"risk":50.398799344536314,"volume":137.98061871901155,"heat":0},{"time":"10:39","price":743.1408066584331,"allow":71.26898712543357,"risk":47.199831150501005,"volume":188.09408168774098,"heat":16.04635812319293},{"time":"10:42","price":743.1675395874163,"allow":68.52227004885447,"risk":41.873908694654716,"volume":183.3746181242168,"heat":7.201073037857306},{"time":"10:45","price":743.1309871986772,"allow":72.3174934920348,"risk":41.148842609420896,"volume":145.77966475393623,"heat":0},{"time":"10:48","price":743.0899590167857,"allow":75.26527460108008,"risk":44.32091261538689,"volume":74.22796973027289,"heat":8.000357246306429},{"time":"10:51","price":743.1864574505499,"allow":78.3634289651648,"risk":43.77349142637571,"volume":136.94642895366997,"heat":23.433258372373892},{"time":"10:54","price":743.0504360895308,"allow":71.45770025909164,"risk":40.66040921471124,"volume":49.79509074706584,"heat":18.532089131537635},{"time":"10:57","price":743.0503894807854,"allow":74.52533153800746,"risk":37.07889816350616,"volume":132.40153725724667,"heat":57.42916407534941},{"time":"10:00","price":742.8383626821148,"allow":78.8478647003533,"risk":37.51120951120008,"volume":139.38808912411332,"heat":45.22116087886407},{"time":"10:03","price":742.7035094290563,"allow":73.20856579303629,"risk":35.771541092989345,"volume":145.19354282412678,"heat":62.81488881153997},{"time":"10:06","price":742.4575783167586,"allow":74.14340055324293,"risk":36.6335550951636,"volume":216.60756948869675,"heat":46.57436082206949},{"time":"10:09","price":742.0781182460115,"allow":74.53889133371274,"risk":33.38034805096508,"volume":194.50963626615703,"heat":33.80056576210533},{"time":"10:12","price":741.8765597339055,"allow":77.93663492140718,"risk":29.725031860948086,"volume":189.65307033155113,"heat":28.92804429965116},{"time":"10:15","price":741.9677224860988,"allow":77.45227824329365,"risk":33.636709732434866,"volume":196.18277586996555,"heat":80.9340806558644},{"time":"10:18","price":741.8252187427465,"allow":81.18940940940672,"risk":32.12714613628604,"volume":171.13525180146098,"heat":81.78364657943948},{"time":"10:21","price":741.5182844944987,"allow":80.58922739808128,"risk":24.055251418307776,"volume":129.4111137604341,"heat":43.298923823352496},{"time":"11:24","price":741.2434701625543,"allow":77.98313402381977,"risk":29.10367893155327,"volume":198.24534204788506,"heat":17.179426956758057},{"time":"11:27","price":741.0979894599717,"allow":79.52593011669569,"risk":24.937621117656775,"volume":62.36588376574218,"heat":26.19578220869502},{"time":"11:30","price":740.8940501887362,"allow":78.4756115501442,"risk":24.663265943359992,"volume":121.35426842141896,"heat":12.252054216595717},{"time":"11:33","price":741.0814739126787,"allow":82.44624712678986,"risk":20.905942190658156,"volume":210.70726960897446,"heat":27.81639351924214},{"time":"11:36","price":741.2052910881109,"allow":80.84776304746676,"risk":22.91901827929177,"volume":50.48745384439826,"heat":38.3862323483496},{"time":"11:39","price":741.0809661742069,"allow":80.12293691374309,"risk":22.40382459621745,"volume":104.56935250665992,"heat":10.712623614284482},{"time":"11:42","price":741.0613646540387,"allow":78.60366782221149,"risk":18.99395329261702,"volume":111.59007051959634,"heat":0},{"time":"11:45","price":741.0787950867469,"allow":76.38466702886575,"risk":24.994597067563475,"volume":183.14267116598785,"heat":0},{"time":"11:48","price":741.5357573873116,"allow":74.26147119658799,"risk":21.300001112576066,"volume":215.79231277108192,"heat":19.213246785679953},{"time":"11:51","price":741.6822415217924,"allow":75.09581032241957,"risk":18.319974018916287,"volume":113.63917598966509,"heat":19.055094134904273},{"time":"11:54","price":741.9226692583725,"allow":78.86871245885848,"risk":22.576478305953923,"volume":132.4178856983781,"heat":17.499091496500668},{"time":"11:57","price":742.1790445669274,"allow":73.47813128290848,"risk":16.166921624835016,"volume":40.33718690741807,"heat":19.912444752507934},{"time":"11:00","price":742.4173374960766,"allow":72.43042342735039,"risk":22.279902629559917,"volume":108.87264518998563,"heat":39.493046533708885},{"time":"11:03","price":742.650379759118,"allow":78.10123600775789,"risk":24.567482643453857,"volume":99.68211811035872,"heat":42.67154801854972},{"time":"11:06","price":743.0857458801337,"allow":77.53665752001308,"risk":16.692893934494684,"volume":102.70678830333054,"heat":60.23617812331153},{"time":"11:09","price":743.3542745089177,"allow":71.96469690712574,"risk":20.09987658400805,"volume":89.69633822795004,"heat":85.55917404604314},{"time":"11:12","price":743.7854436072334,"allow":70.41931733079174,"risk":24.42596120480691,"volume":196.89462831709534,"heat":87.72986695607526},{"time":"11:15","price":744.1831411046325,"allow":71.13609330137984,"risk":21.12351212554307,"volume":69.50429053045809,"heat":72.41383540513907},{"time":"11:18","price":744.144042068691,"allow":74.87619471566443,"risk":25.666681869651327,"volume":181.9645484071225,"heat":99.27902982221005},{"time":"11:21","price":744.0525975438427,"allow":75.05757821310067,"risk":25.187586988163996,"volume":164.96226300485432,"heat":78.99298443616829},{"time":"11:24","price":744.1867840858295,"allow":68.74667176776286,"risk":24.608971529383616,"volume":156.723665734753,"heat":91.7073156488149},{"time":"11:27","price":744.4234903949019,"allow":66.05400364474902,"risk":23.616919928306444,"volume":61.62036993075162,"heat":100},{"time":"11:30","price":744.3842533091473,"allow":70.38686911077637,"risk":22.501005729794972,"volume":117.53278349991888,"heat":87.9181706523827},{"time":"11:33","price":744.6242788444348,"allow":70.13803562822723,"risk":21.662867983846255,"volume":188.94599925726652,"heat":89.87311031952649},{"time":"12:36","price":744.8351105327638,"allow":66.59142141361026,"risk":21.568109690300286,"volume":82.64572393614799,"heat":79.27724858100889},{"time":"12:39","price":744.7441453773798,"allow":67.20266584892057,"risk":27.27567929523417,"volume":81.43551005516201,"heat":79.24898728164743},{"time":"12:42","price":744.968477750466,"allow":62.9255915058901,"risk":26.401486364034106,"volume":91.25615219585598,"heat":58.445503910333315},{"time":"12:45","price":744.8107331933107,"allow":68.22013735285604,"risk":30.61497426376572,"volume":156.24336751177907,"heat":77.18794254763134},{"time":"12:48","price":744.835022617049,"allow":64.8547549156945,"risk":32.49793021674886,"volume":184.88864146173,"heat":89.42834389081742},{"time":"12:51","price":744.8723308737164,"allow":65.63042000247106,"risk":30.200632010694562,"volume":179.9229453271255,"heat":95.1649932217598},{"time":"12:54","price":745.1776403101163,"allow":60.17793375880621,"risk":32.9810753934142,"volume":145.71649294812232,"heat":48.18280712618769},{"time":"12:57","price":745.3873440282489,"allow":56.50252790113614,"risk":34.98674232706432,"volume":167.87260747514665,"heat":35.46203640626434},{"time":"12:00","price":745.2207551324364,"allow":58.71532774403549,"risk":35.90254876231082,"volume":149.1076986119151,"heat":58.359217041167156},{"time":"12:03","price":745.2134181726685,"allow":56.600061645509,"risk":32.04866638057989,"volume":196.5241965185851,"heat":69.81436309806534},{"time":"12:06","price":745.1794377274596,"allow":56.51545538142533,"risk":38.84878836625237,"volume":190.00581241678447,"heat":90.15851580400724},{"time":"12:09","price":745.4260691126216,"allow":54.45223461311279,"risk":35.10105568143571,"volume":127.67569900490344,"heat":66.31653120289727},{"time":"12:12","price":745.5865986341545,"allow":51.79050192827379,"risk":39.88066904155176,"volume":51.2000625487417,"heat":73.3350361212223},{"time":"12:15","price":745.7341805763734,"allow":53.60164111242388,"risk":43.901139198202735,"volume":160.667672958225,"heat":56.65450994405303},{"time":"12:18","price":745.7583770072582,"allow":49.59574056103966,"risk":46.39767570156306,"volume":46.79418961983174,"heat":66.65130565164034},{"time":"12:21","price":745.6088535815624,"allow":54.71295788493155,"risk":40.00621120335429,"volume":51.18781524710357,"heat":84.51588914093426},{"time":"12:24","price":745.8158015421224,"allow":49.72098011039653,"risk":48.17928222703983,"volume":131.59997640177608,"heat":68.0005909304974},{"time":"12:27","price":745.9529167014365,"allow":50.57656208354687,"risk":43.16611610372498,"volume":47.240815977565944,"heat":63.80847481391662},{"time":"12:30","price":745.958494652258,"allow":52.85457752472702,"risk":50.39505448317179,"volume":180.88173132389784,"heat":75.57642568921304},{"time":"12:33","price":745.843375092101,"allow":45.10236850856238,"risk":46.998149654933464,"volume":113.04551315493882,"heat":80.61978323311371},{"time":"12:36","price":745.7123053247377,"allow":44.42183704256136,"risk":47.072340371954176,"volume":152.25948464125395,"heat":93.94120561762628},{"time":"12:39","price":745.9204697664186,"allow":49.77871432253496,"risk":53.61865003003427,"volume":217.365747038275,"heat":58.79916615192525},{"time":"12:42","price":745.834337370563,"allow":43.837933575448055,"risk":47.502658856748226,"volume":217.10139865987003,"heat":49.459711764192946},{"time":"12:45","price":745.8257569772873,"allow":42.02269846894896,"risk":50.13118090801741,"volume":52.69309114664793,"heat":38.20695940828206},{"time":"13:48","price":745.5428077746683,"allow":46.585891041782844,"risk":52.753477366828896,"volume":184.33380628470331,"heat":55.34341231046946},{"time":"13:51","price":745.3959387004679,"allow":41.17959771736812,"risk":50.54304569707472,"volume":65.48157585319132,"heat":41.43598490068392},{"time":"13:54","price":745.0440831248712,"allow":39.86170231414434,"risk":56.30401077326791,"volume":196.73616169020534,"heat":58.309112463531875},{"time":"13:57","price":744.7095792334202,"allow":40.85937146235681,"risk":53.39946281975282,"volume":66.188521576114,"heat":87.9526419083288},{"time":"13:00","price":744.6418110887012,"allow":38.1823764740455,"risk":54.57031851064543,"volume":188.57006473932415,"heat":60.15511483938195},{"time":"13:03","price":744.3289516256256,"allow":40.75968974389389,"risk":60.21409682043597,"volume":41.49700384121388,"heat":59.297436968769304},{"time":"13:06","price":744.0859303064856,"allow":41.79007811793453,"risk":57.487035838999674,"volume":132.29227914940566,"heat":62.43732128289003},{"time":"13:09","price":743.80812828221,"allow":42.31819975673268,"risk":58.59129719115768,"volume":199.03207762166858,"heat":74.85296722845574},{"time":"13:12","price":743.6979555742597,"allow":38.20397436876667,"risk":62.87131245572578,"volume":136.3166952272877,"heat":45.36204769075344},{"time":"13:15","price":743.3053331800353,"allow":35.70905596218586,"risk":59.62656264050762,"volume":175.83908810280263,"heat":78.18475509142345},{"time":"13:18","price":743.2014875455598,"allow":36.47270443305895,"risk":63.55386266680693,"volume":215.03206635825336,"heat":63.30404600723648},{"time":"13:21","price":743.1495917909326,"allow":38.7619003851759,"risk":58.44098578074491,"volume":117.95167824719101,"heat":37.338258254696164},{"time":"13:24","price":742.7824110631294,"allow":37.2578725761632,"risk":62.809117231611964,"volume":127.20118965953588,"heat":74.56312137073564},{"time":"13:27","price":742.5328605342198,"allow":38.89742549525907,"risk":60.040053296643606,"volume":46.32944988552481,"heat":91.4514271280221},{"time":"13:30","price":742.5579176892568,"allow":37.91014826334149,"risk":57.11853478347901,"volume":140.66745722666383,"heat":69.49040075392963},{"time":"13:33","price":742.3696219481459,"allow":34.692573762941265,"risk":56.01701348751124,"volume":194.70723686739802,"heat":94.7340257015607},{"time":"13:36","price":742.2742967555215,"allow":38.84985032126258,"risk":54.14321074422008,"volume":107.93822781648487,"heat":92.26407865458975},{"time":"13:39","price":742.1469627660425,"allow":35.85351900113547,"risk":55.12032823670941,"volume":197.19016265589744,"heat":94.88689798563914},{"time":"13:42","price":742.0723433116394,"allow":38.41480451027773,"risk":55.2148774150327,"volume":133.75982600729913,"heat":87.29911068461134},{"time":"13:45","price":742.0883100861652,"allow":38.04302679125401,"risk":56.170605644666765,"volume":145.02266532275826,"heat":79.14556084082628},{"time":"13:48","price":742.2670280337387,"allow":36.12261067288893,"risk":56.034001277130855,"volume":58.74659385997802,"heat":91.69707974066529},{"time":"13:51","price":742.1914209327787,"allow":38.88523174843835,"risk":52.98743145050994,"volume":130.80810469109565,"heat":85.53358236202934},{"time":"13:54","price":742.4814046891084,"allow":36.52091286672318,"risk":53.032245463254085,"volume":110.34020093269646,"heat":100},{"time":"13:57","price":742.4185070778015,"allow":40.48187484507448,"risk":57.076071158193805,"volume":41.177523410879076,"heat":85.21965925540974},{"time":"14:00","price":742.3166608549664,"allow":40.69866487908017,"risk":53.49802959942403,"volume":182.38684985321015,"heat":64.00254451481496},{"time":"14:03","price":742.6179002095791,"allow":42.64261493747445,"risk":50.29024691003474,"volume":147.75205824989825,"heat":80.38775586874144},{"time":"14:06","price":742.8803902273675,"allow":43.79033004489379,"risk":53.993599252424985,"volume":110.21295635029674,"heat":82.34271574530877},{"time":"14:09","price":743.042547993742,"allow":41.61093778624148,"risk":48.74219273049125,"volume":159.267424819991,"heat":80.51637067277434},{"time":"14:12","price":743.3001899796353,"allow":43.66116770543838,"risk":52.10246943885737,"volume":141.11786663066596,"heat":55.27576862362177},{"time":"14:15","price":743.4688665017586,"allow":45.372444322457596,"risk":47.66569104621081,"volume":163.02984988782555,"heat":51.563075906813445},{"time":"14:18","price":743.3869651356642,"allow":41.68439217329743,"risk":44.93483393455954,"volume":130.51890769973397,"heat":66.3215183132632},{"time":"14:21","price":743.4580411008803,"allow":46.394958824780005,"risk":43.51848201619335,"volume":207.40250860806555,"heat":63.52804049089632},{"time":"14:24","price":743.5987281023741,"allow":41.337725525143746,"risk":47.151996702803,"volume":102.44165051728487,"heat":37.63775008113296},{"time":"14:27","price":743.5860524497101,"allow":44.5991793004539,"risk":42.15579924400075,"volume":199.1086238855496,"heat":41.192325786883934},{"time":"14:30","price":743.711978813866,"allow":46.40968430335715,"risk":43.42627239150949,"volume":118.4556773910299,"heat":25.038172119139524},{"time":"14:33","price":743.6101778380983,"allow":47.793895388627625,"risk":38.42074553066334,"volume":107.13527937885374,"heat":57.990195754072715},{"time":"14:36","price":743.6266116184638,"allow":51.250791735508884,"risk":41.074149420443135,"volume":81.44552869256586,"heat":49.77992157895176},{"time":"14:39","price":743.4628903456512,"allow":45.076008924315865,"risk":38.178799178319096,"volume":59.103259765543044,"heat":89.7204196169672},{"time":"14:42","price":743.73910966743,"allow":50.03883959685376,"risk":35.38743188943374,"volume":54.204408596269786,"heat":52.343371930552294},{"time":"14:45","price":743.8713663695336,"allow":54.248390958247995,"risk":33.50705616575104,"volume":95.99660312291235,"heat":56.147506816144336},{"time":"14:48","price":744.1433726320943,"allow":50.03484627764634,"risk":31.03429150366056,"volume":90.36534117069095,"heat":15.28415217926904},{"time":"14:51","price":744.4114239091989,"allow":48.91789644244144,"risk":33.89073788660682,"volume":41.34855597745627,"heat":0},{"time":"14:54","price":744.6804430270519,"allow":56.43196281211799,"risk":32.04249745605533,"volume":53.540302026085556,"heat":0},{"time":"14:57","price":744.6617523521713,"allow":56.508292573197274,"risk":31.73019985219537,"volume":55.670061185956,"heat":9.988519868468742},{"time":"14:00","price":744.766022613199,"allow":54.744298358728486,"risk":29.90513182294898,"volume":215.04381191916764,"heat":34.56291965416612},{"time":"14:03","price":744.9150372188,"allow":58.29710738960511,"risk":24.272398629189983,"volume":175.836259922944,"heat":46.77950870100689},{"time":"14:06","price":744.9253696684257,"allow":59.33068503436124,"risk":19.577787041128595,"volume":47.493685549125075,"heat":68.05796824059732},{"time":"14:09","price":745.3128453761833,"allow":58.71267587355765,"risk":26.75459663589219,"volume":244.9356179079041,"heat":48.78944181047721},{"time":"15:12","price":745.3268254763926,"allow":58.902586542136746,"risk":24.089438435161526,"volume":192.3411599220708,"heat":60.354606693083866},{"time":"15:15","price":745.3856907104146,"allow":60.49066816892188,"risk":23.42031230229883,"volume":181.4773118123412,"heat":93.21210536709445},{"time":"15:18","price":745.7005541577735,"allow":60.79821572780415,"risk":18.83068149737663,"volume":216.35580331087112,"heat":76.13075271216103},{"time":"15:21","price":745.9641828034516,"allow":63.452675039818004,"risk":18.956880343338618,"volume":193.61765646841377,"heat":54.27098675413822},{"time":"15:24","price":746.0017315609254,"allow":66.02956764124743,"risk":16.982354550008193,"volume":159.40813027787954,"heat":85.35351257806136},{"time":"15:27","price":746.3432600169759,"allow":63.01522127912841,"risk":16.58396801594805,"volume":176.9421439198777,"heat":42.253175661424585},{"time":"15:30","price":746.471853493303,"allow":64.4643585811807,"risk":17.26619766506468,"volume":206.88823434058577,"heat":31.57522760081836},{"time":"15:33","price":746.29733137477,"allow":73.27403206985667,"risk":14.414283164025576,"volume":242.98089094925672,"heat":63.254869831442505},{"time":"15:36","price":746.2237255366921,"allow":72.47921267573862,"risk":11.254012135018167,"volume":160.01496833283454,"heat":87.33508813945178},{"time":"15:39","price":746.1932236939048,"allow":70.98362538542588,"risk":12.180101375924675,"volume":212.1304154302925,"heat":74.93024520565652},{"time":"15:42","price":746.3488880873675,"allow":73.06865219730068,"risk":12.296529345321222,"volume":293.9590563206002,"heat":58.09715137851048},{"time":"15:45","price":746.2617749953417,"allow":74.13372523926137,"risk":15.968812921104254,"volume":298.32303025294095,"heat":62.732816306409845},{"time":"15:48","price":745.9953920231831,"allow":76.96497347648247,"risk":15.524445903629886,"volume":175.6639556121081,"heat":67.46855678339023},{"time":"15:51","price":745.883942037925,"allow":76.650815722728,"risk":14.262136046683427,"volume":240.25679894722998,"heat":73.7341576646186},{"time":"15:54","price":745.8275053650165,"allow":78.20316555761451,"risk":11.442316275755298,"volume":141.52421697974205,"heat":43.63751104795336},{"time":"15:57","price":745.7,"allow":76.20130777957107,"risk":11.348997759298218,"volume":167.15799155645072,"heat":42.38213697359239}]};
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const COLORS = {
    bg: "#05060d",
    panel: "rgba(255,255,255,.04)",
    grid: "rgba(220,205,255,.08)",
    text: "#f5f0ff",
    muted: "#9e96ad",
    good: "#21e295",
    goodSoft: "rgba(33,226,149,.14)",
    bad: "#ff4e74",
    badSoft: "rgba(255,78,116,.16)",
    warn: "#f6b84a",
    warnSoft: "rgba(246,184,74,.16)",
    purple: "#9c67ff",
    purpleSoft: "rgba(156,103,255,.16)",
    gold: "#e3b64d",
    cyan: "#3bd7ff",
    blue: "#4f7cff",
    white: "#f5f0ff"
  };

  const state = {
    candles: [],
    drawings: [],
    bracket: null,
    activeTool: "cursor",
    locked: false,
    edge: null,
    layers: { emas: true, sr: true, heat: true, vcp: true, mae: true },
    hover: null,
    drag: null,
    tempDrawing: null,
    supports: [],
    pivots: [],
    indicators: {},
    atr: 0,
    vcp: null,
    plan: null,
    themeRoyal: false,
    market: {
      candleSymbol: "BTCUSDT",
      candleTimeframe: "5m",
      candleSource: "live-data",
    },
    backend: {
      data: null,
      exchanges: [],
      platforms: [],
      strategies: [],
      brackets: [],
      bracketHealth: null,
      bracketRisk: null,
      coverage: null,
      warFeatures: null,
      warAnalysis: null,
      warTicket: null,
      parsedSignal: null,
      signalPreview: null,
      ticketPayload: null,
      ticketPreview: null,
      deskTable: "positions",
      strategyPins: readLocalJson("sentinelGuardianPinnedStrategies", []),
      autoRefreshTimer: null,
      autoRefreshEnabled: false,
      selectedVenueJson: null,
      liveStatus: null,
      livePreview: null,
      livePreviewId: null,
      edgeLatest: null,
      serverDrawings: null,
      drawingSavePending: null,
      edgeStream: null,
      edgeConnected: false,
      edgeEventCount: 0,
      candleStream: null,
      candleConnected: false,
      candleEventCount: 0,
    },
  };

  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
  function safeNumber(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }
  function pct(value) { return Number.isFinite(value) ? `${value.toFixed(2)}%` : "--"; }
  function money(value) { return Number.isFinite(value) ? `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "--"; }
  function qtyFmt(value) {
    if (!Number.isFinite(value)) return "--";
    if (Math.abs(value) >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (Math.abs(value) >= 1) return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
    return value.toLocaleString(undefined, { maximumFractionDigits: 8 });
  }
  function priceFmt(value) {
    if (!Number.isFinite(value)) return "--";
    const abs = Math.abs(value);
    if (abs >= 10000) return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
    if (abs >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (abs >= 1) return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
    return value.toLocaleString(undefined, { maximumFractionDigits: 8 });
  }
  function titleCase(value) {
    return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
  }
  function toast(message) {
    const el = $("#toast");
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.remove("show"), 2400);
  }

  function createRng(seed) {
    let s = seed >>> 0;
    return () => {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  function currentSymbol() { return ($("#symbolInput").value || "BTCUSDT").trim().toUpperCase(); }
  function currentTimeframe() { return $("#timeframeInput").value || "5m"; }
  function setCurrentSymbol(symbol) {
    const normalized = rawSymbol(symbol);
    const main = $("#symbolInput"); if (main) main.value = normalized;
    const ticket = $("#ticketSymbolInput"); if (ticket) ticket.value = normalized;
    const mark = $("#markSymbolInput"); if (mark) mark.value = normalized;
    return normalized;
  }
  function markCandleSeries(symbol = currentSymbol(), timeframe = currentTimeframe(), source = "live-data") {
    state.market.candleSymbol = rawSymbol(symbol);
    state.market.candleTimeframe = timeframe;
    state.market.candleSource = source;
  }
  function chartMatchesSymbol(symbol = currentSymbol(), timeframe = currentTimeframe()) {
    return state.market.candleSymbol === rawSymbol(symbol) && state.market.candleTimeframe === timeframe;
  }
  function latestChartPriceFor(symbol = currentSymbol(), timeframe = currentTimeframe()) {
    if (!chartMatchesSymbol(symbol, timeframe)) return null;
    const close = state.candles.at(-1)?.close;
    return Number.isFinite(close) ? close : null;
  }
  function resetDeskSymbolFields({ keepSize = true } = {}) {
    ["ticketPriceInput", "ticketStopInput", "ticketTakeProfitInput", "ticketTrailingInput", "ticketTrailActivationInput", "ticketBreakevenInput"].forEach(id => {
      const el = $("#" + id);
      if (el) el.value = "";
    });
    if (!keepSize) {
      const size = $("#ticketSizeInput");
      if (size) size.value = "100";
    }
    state.backend.ticketPayload = null;
    state.backend.ticketPreview = null;
    state.backend.livePreview = null;
    state.backend.livePreviewId = null;
    const previewId = $("#livePreviewIdInput"); if (previewId) previewId.value = "";
  }
  function syncMarkPriceFromChart() {
    const mark = $("#markPriceInput");
    const latest = latestChartPriceFor(currentSymbol());
    if (mark) mark.value = Number.isFinite(latest) ? round(latest, 8) : "";
  }
  function live-dataReferencePrice(symbol) {
    const normalized = rawSymbol(symbol);
    if (normalized.includes("ETH")) return 3250;
    if (normalized.includes("SOL")) return 154;
    if (normalized.includes("XAU")) return 2743;
    return 67240;
  }

  function generateCandles(symbol, bars, scenario) {
    const seed = Array.from(symbol + scenario).reduce((a, ch) => a + ch.charCodeAt(0), 0) + bars * 17;
    const rng = createRng(seed);
    const base = symbol.includes("ETH") ? 3250 : symbol.includes("SOL") ? 154 : symbol.includes("XAU") ? 2743 : 67240;
    const candles = [];
    let close = base * (0.985 + rng() * 0.03);
    let trend = scenario === "trend" ? 0.0016 : scenario === "range" ? 0.00008 : scenario === "vcp" ? 0.0011 : 0.00055;
    for (let i = 0; i < bars; i++) {
      let volRegime = scenario === "volatile" ? 0.010 + rng() * 0.010 : 0.006 + rng() * 0.005;
      let drift = trend;
      let wave = Math.sin(i / 7.5) * volRegime * 0.45 + Math.sin(i / 21) * volRegime * 0.6;
      if (scenario === "range") {
        drift = Math.sin(i / 14) * 0.0001;
        wave = Math.sin(i / 5.2) * 0.0032 + Math.sin(i / 19) * 0.0042;
      }
      if (scenario === "vcp") {
        const t = i / Math.max(1, bars - 1);
        if (t < 0.36) {
          drift = 0.0017;
          volRegime = 0.009;
          wave = Math.sin(i / 4.8) * 0.004;
        } else if (t < 0.54) {
          drift = -0.00005;
          volRegime = 0.0090;
          wave = Math.sin(i / 4.2) * 0.0072;
        } else if (t < 0.70) {
          drift = 0.00010;
          volRegime = 0.0055;
          wave = Math.sin(i / 4.7) * 0.0045;
        } else if (t < 0.84) {
          drift = 0.00012;
          volRegime = 0.0034;
          wave = Math.sin(i / 5.5) * 0.0026;
        } else if (t < 0.94) {
          drift = 0.00008;
          volRegime = 0.0021;
          wave = Math.sin(i / 6.1) * 0.0014;
        } else {
          drift = 0.0019;
          volRegime = 0.0048;
          wave = Math.sin(i / 5.7) * 0.0014;
        }
      }
      const shock = (rng() - 0.5) * volRegime;
      if (scenario === "volatile" && (i % 37 === 0 || i % 53 === 0) && i > 10) {
        close *= 1 + (rng() > 0.5 ? 1 : -1) * (0.012 + rng() * 0.016);
      }
      const open = close;
      close = Math.max(0.0001, close * (1 + drift + wave * 0.18 + shock));
      const bodyHigh = Math.max(open, close);
      const bodyLow = Math.min(open, close);
      const wick = volRegime * (0.42 + rng() * 0.75);
      const high = bodyHigh * (1 + wick);
      const low = Math.max(0.0001, bodyLow * (1 - wick * (0.85 + rng() * 0.55)));
      const volBase = symbol.includes("BTC") ? 1850 : 950;
      const contractionVolume = scenario === "vcp" ? (1.3 - (i / bars) * 0.72) : 1;
      const volume = Math.max(10, volBase * contractionVolume * (0.65 + rng() * 1.2) * (1 + Math.abs(close - open) / open * 16));
      candles.push({
        time: labelForIndex(i, currentTimeframe()),
        open: round(open), high: round(high), low: round(low), close: round(close), volume: round(volume, 2)
      });
    }
    return candles;
  }

  function labelForIndex(i, tf) {
    const baseMinutes = 9 * 60 + 30;
    const step = tf.endsWith("m") ? Number(tf.replace("m", "")) || 5 : tf === "1h" ? 60 : tf === "4h" ? 240 : 5;
    const total = baseMinutes + i * step;
    const h = Math.floor(total / 60) % 24;
    const m = total % 60;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
  }
  function round(value, digits = 8) {
    const f = 10 ** digits;
    return Math.round(value * f) / f;
  }

  function edgeToCandles(packet) {
    const series = Array.isArray(packet.series) ? packet.series : [];
    const candles = [];
    let prev = safeNumber(packet.current_price, 100);
    series.forEach((pt, i) => {
      const close = safeNumber(pt.price, prev);
      const open = prev;
      const heat = safeNumber(pt.heat, 50) / 100;
      const vol = safeNumber(pt.volume, 100);
      const spread = Math.max(0.0005, 0.00065 + heat * 0.0012 + Math.abs(close - open) / Math.max(1, close) * 0.5);
      const high = Math.max(open, close) * (1 + spread);
      const low = Math.min(open, close) * (1 - spread);
      candles.push({ time: pt.time || labelForIndex(i, "3m"), open: round(open, 6), high: round(high, 6), low: round(low, 6), close: round(close, 6), volume: round(vol, 2) });
      prev = close;
    });
    return candles;
  }

  function sma(values, period) {
    const out = Array(values.length).fill(null);
    let sum = 0;
    for (let i = 0; i < values.length; i++) {
      sum += values[i];
      if (i >= period) sum -= values[i - period];
      if (i >= period - 1) out[i] = sum / period;
    }
    return out;
  }
  function ema(values, period) {
    const out = Array(values.length).fill(null);
    const k = 2 / (period + 1);
    let prev = null;
    for (let i = 0; i < values.length; i++) {
      const v = values[i];
      if (prev === null) {
        if (i >= period - 1) {
          const seed = values.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period;
          prev = seed;
          out[i] = seed;
        }
      } else {
        prev = v * k + prev * (1 - k);
        out[i] = prev;
      }
    }
    return out;
  }
  function atrSeries(candles, period = 14) {
    const tr = candles.map((c, i) => {
      if (i === 0) return c.high - c.low;
      const prev = candles[i - 1].close;
      return Math.max(c.high - c.low, Math.abs(c.high - prev), Math.abs(c.low - prev));
    });
    return ema(tr, period);
  }
  function avg(arr) { return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0; }
  function lastNonNull(arr, fallback = null) {
    for (let i = arr.length - 1; i >= 0; i--) if (arr[i] !== null && arr[i] !== undefined && Number.isFinite(arr[i])) return arr[i];
    return fallback;
  }

  function detectPivots(candles, span = 3) {
    const pivots = [];
    for (let i = span; i < candles.length - span; i++) {
      let isHigh = true, isLow = true;
      for (let j = i - span; j <= i + span; j++) {
        if (j === i) continue;
        if (candles[j].high >= candles[i].high) isHigh = false;
        if (candles[j].low <= candles[i].low) isLow = false;
      }
      if (isHigh) pivots.push({ kind: "high", index: i, price: candles[i].high, time: candles[i].time });
      if (isLow) pivots.push({ kind: "low", index: i, price: candles[i].low, time: candles[i].time });
    }
    return pivots.sort((a, b) => a.index - b.index);
  }

  function clusterLevels(candles, pivots, atrValue) {
    const tol = Math.max(atrValue * 0.55, (Math.max(...candles.map(c => c.high)) - Math.min(...candles.map(c => c.low))) * 0.006);
    const clusters = [];
    const items = pivots.slice(-80).map(p => ({ ...p }));
    for (const p of items) {
      let cluster = clusters.find(c => Math.abs(c.price - p.price) <= tol);
      if (!cluster) {
        cluster = { price: p.price, touches: 0, kinds: new Set(), indices: [], volume: 0 };
        clusters.push(cluster);
      }
      cluster.touches += 1;
      cluster.kinds.add(p.kind);
      cluster.indices.push(p.index);
      cluster.volume += candles[p.index]?.volume || 0;
      cluster.price = (cluster.price * (cluster.touches - 1) + p.price) / cluster.touches;
    }
    const last = candles.at(-1)?.close || 0;
    return clusters.map(c => {
      const kind = c.price <= last ? "support" : "resistance";
      const recency = Math.max(...c.indices) / Math.max(1, candles.length - 1);
      const distance = Math.abs(c.price - last) / Math.max(1e-9, last);
      return {
        kind,
        price: c.price,
        zoneLow: c.price - tol * 0.48,
        zoneHigh: c.price + tol * 0.48,
        touches: c.touches,
        score: c.touches * 12 + recency * 10 - distance * 100,
        lastIndex: Math.max(...c.indices)
      };
    }).sort((a, b) => b.score - a.score).slice(0, 12);
  }

  function detectVCP(candles, pivots) {
    const recentStart = Math.max(0, candles.length - 115);
    const recentPivots = pivots.filter(p => p.index >= recentStart);
    const pairs = [];
    let lastHigh = null;
    for (const p of recentPivots) {
      if (p.kind === "high") {
        if (!lastHigh || p.price > lastHigh.price * 0.985) lastHigh = p;
      } else if (p.kind === "low" && lastHigh && p.index > lastHigh.index) {
        const volumeSlice = candles.slice(lastHigh.index, p.index + 1).map(c => c.volume);
        pairs.push({
          startIndex: lastHigh.index,
          endIndex: p.index,
          high: lastHigh.price,
          low: p.price,
          pct: Math.max(0, (lastHigh.price - p.price) / lastHigh.price * 100),
          volume: avg(volumeSlice)
        });
        lastHigh = null;
      }
    }
    const contractions = pairs.filter(p => p.pct > 0.12).slice(-5);
    let shrink = 0, volDry = 0;
    for (let i = 1; i < contractions.length; i++) {
      if (contractions[i].pct < contractions[i - 1].pct * 0.92) shrink += 1;
      if (contractions[i].volume < contractions[i - 1].volume * 0.98) volDry += 1;
    }
    const highs = candles.slice(recentStart).map(c => c.high);
    const lows = candles.slice(recentStart).map(c => c.low);
    const pivot = Math.max(...highs);
    const low = Math.min(...lows);
    const lastClose = candles.at(-1)?.close || 0;
    const nearPivot = pivot ? clamp(100 - Math.abs(pivot - lastClose) / pivot * 1000, 0, 100) : 0;
    const finalLow = contractions.at(-1)?.low || low;
    const validCount = contractions.length >= 2 ? 24 : contractions.length * 8;
    const score = clamp(validCount + shrink * 18 + volDry * 14 + nearPivot * 0.22, 0, 100);
    const status = score >= 72 ? "Clean VCP candidate" : score >= 48 ? "Developing contraction" : "No clean VCP yet";
    return { score, status, contractions, pivot, finalLow, shrink, volDry, nearPivot };
  }

  function computeIndicators() {
    const closes = state.candles.map(c => c.close);
    state.indicators = {
      ema20: ema(closes, 20),
      ema50: ema(closes, 50),
      ema200: ema(closes, 120),
      sma20: sma(closes, 20),
      atr14: atrSeries(state.candles, 14),
    };
    state.atr = lastNonNull(state.indicators.atr14, Math.max(1e-9, (Math.max(...state.candles.map(c => c.high)) - Math.min(...state.candles.map(c => c.low))) / 40));
    state.pivots = detectPivots(state.candles, 3);
    state.supports = clusterLevels(state.candles, state.pivots, state.atr);
    state.vcp = detectVCP(state.candles, state.pivots);
  }

  function chartBounds(canvas) {
    const rect = canvas.getBoundingClientRect();
    const pad = { left: 64, right: 112, top: 24, bottom: 28 };
    const priceBottom = Math.max(240, rect.height - 108);
    let min = Math.min(...state.candles.map(c => c.low));
    let max = Math.max(...state.candles.map(c => c.high));
    const include = (p) => { if (Number.isFinite(p)) { min = Math.min(min, p); max = Math.max(max, p); } };
    state.supports.forEach(l => { include(l.zoneLow); include(l.zoneHigh); });
    if (state.edge) {
      (state.edge.levels || []).forEach(l => { include(l.support); include(l.resistance); include(l.price); });
      include(state.edge.support); include(state.edge.resistance); include(state.edge.max_pain);
    }
    if (state.bracket) [state.bracket.entry, state.bracket.stop, state.bracket.tp1, state.bracket.tp2, state.plan?.liquidation].forEach(include);
    state.drawings.forEach(d => {
      if (d.type === "trend") { include(d.a.price); include(d.b.price); }
      if (d.type === "hline") include(d.price);
      if (d.type === "zone") { include(d.a.price); include(d.b.price); }
    });
    if (state.tempDrawing) {
      const d = state.tempDrawing;
      if (d.type === "trend") { include(d.a.price); include(d.b.price); }
      if (d.type === "zone") { include(d.a.price); include(d.b.price); }
    }
    const spread = Math.max(1e-9, max - min);
    min -= spread * 0.12;
    max += spread * 0.12;
    const innerW = Math.max(1, rect.width - pad.left - pad.right);
    const innerH = Math.max(1, priceBottom - pad.top);
    const x = (index) => pad.left + (index / Math.max(1, state.candles.length - 1)) * innerW;
    const y = (price) => pad.top + (1 - (price - min) / Math.max(1e-9, max - min)) * innerH;
    const priceAtY = (yy) => max - ((yy - pad.top) / innerH) * (max - min);
    const indexAtX = (xx) => clamp(Math.round(((xx - pad.left) / innerW) * (state.candles.length - 1)), 0, state.candles.length - 1);
    return { rect, pad, min, max, innerW, innerH, priceBottom, volTop: rect.height - 88, volBottom: rect.height - 30, x, y, priceAtY, indexAtX };
  }

  function setupCanvas(canvas) {
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = Math.floor(rect.width * ratio);
    const h = Math.floor(rect.height * ratio);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { ctx, width: rect.width, height: rect.height };
  }

  function drawGrid(ctx, b, width, height) {
    ctx.clearRect(0, 0, width, height);
    const bg = ctx.createLinearGradient(0, 0, 0, height);
    bg.addColorStop(0, "#080713");
    bg.addColorStop(0.6, "#060712");
    bg.addColorStop(1, "#05050a");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    ctx.font = "11px Inter, sans-serif";
    ctx.fillStyle = COLORS.muted;
    for (let i = 0; i <= 6; i++) {
      const y = b.pad.top + (b.innerH / 6) * i;
      ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(width - b.pad.right + 78, y); ctx.stroke();
      const price = b.max - ((b.max - b.min) / 6) * i;
      ctx.fillText(priceFmt(price), width - b.pad.right + 82, y + 4);
    }
    for (let i = 0; i <= 8; i++) {
      const x = b.pad.left + (b.innerW / 8) * i;
      ctx.beginPath(); ctx.moveTo(x, b.pad.top); ctx.lineTo(x, b.priceBottom); ctx.stroke();
      const idx = Math.round((state.candles.length - 1) * i / 8);
      const label = state.candles[idx]?.time || "";
      ctx.fillText(label, x - 18, height - 9);
    }
    ctx.strokeStyle = "rgba(227,182,77,.14)";
    ctx.beginPath(); ctx.moveTo(b.pad.left, b.volTop); ctx.lineTo(width - b.pad.right + 78, b.volTop); ctx.stroke();
  }

  function drawHeat(ctx, b, width) {
    if (!state.layers.heat) return;
    const levels = [];
    if (state.edge) {
      if (Number.isFinite(state.edge.support)) levels.push({ price: state.edge.support, kind: "support", label: "Edge Support" });
      if (Number.isFinite(state.edge.resistance)) levels.push({ price: state.edge.resistance, kind: "resistance", label: "Edge Resistance" });
      if (Number.isFinite(state.edge.max_pain)) levels.push({ price: state.edge.max_pain, kind: "max", label: "Max Pain" });
    }
    levels.forEach(l => {
      const y = b.y(l.price);
      ctx.fillStyle = l.kind === "support" ? "rgba(33,226,149,.10)" : l.kind === "resistance" ? "rgba(255,78,116,.10)" : "rgba(227,182,77,.10)";
      ctx.fillRect(b.pad.left, y - 12, b.innerW, 24);
      ctx.strokeStyle = l.kind === "support" ? "rgba(33,226,149,.46)" : l.kind === "resistance" ? "rgba(255,78,116,.46)" : "rgba(227,182,77,.46)";
      ctx.setLineDash([6, 5]);
      ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(width - b.pad.right + 76, y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = COLORS.gold;
      ctx.font = "11px Inter, sans-serif";
      ctx.fillText(`${l.label} ${priceFmt(l.price)}`, b.pad.left + 8, y - 7);
    });
  }

  function drawSupportResistance(ctx, b, width) {
    if (!state.layers.sr) return;
    ctx.font = "11px Inter, sans-serif";
    state.supports.slice(0, 8).forEach(level => {
      const y = b.y(level.price);
      const y1 = b.y(level.zoneHigh);
      const y2 = b.y(level.zoneLow);
      const support = level.kind === "support";
      ctx.fillStyle = support ? "rgba(33,226,149,.055)" : "rgba(255,78,116,.055)";
      ctx.strokeStyle = support ? "rgba(33,226,149,.34)" : "rgba(255,78,116,.34)";
      ctx.fillRect(b.pad.left, Math.min(y1, y2), b.innerW, Math.abs(y2 - y1));
      ctx.setLineDash([8, 6]);
      ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(width - b.pad.right + 74, y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = support ? COLORS.good : COLORS.bad;
      ctx.fillText(`${support ? "S" : "R"} ${priceFmt(level.price)} · ${level.touches}x`, b.pad.left + 8, y - 5);
    });
  }

  function drawVCP(ctx, b) {
    if (!state.layers.vcp || !state.vcp?.contractions?.length) return;
    const contractions = state.vcp.contractions;
    ctx.font = "11px Inter, sans-serif";
    contractions.forEach((c, i) => {
      const x1 = b.x(c.startIndex);
      const x2 = b.x(c.endIndex);
      const y1 = b.y(c.high);
      const y2 = b.y(c.low);
      ctx.fillStyle = i === contractions.length - 1 ? "rgba(227,182,77,.12)" : "rgba(156,103,255,.08)";
      ctx.strokeStyle = i === contractions.length - 1 ? "rgba(227,182,77,.48)" : "rgba(156,103,255,.36)";
      ctx.fillRect(x1, Math.min(y1, y2), Math.max(8, x2 - x1), Math.abs(y2 - y1));
      ctx.strokeRect(x1, Math.min(y1, y2), Math.max(8, x2 - x1), Math.abs(y2 - y1));
      ctx.fillStyle = COLORS.gold;
      ctx.fillText(`${c.pct.toFixed(1)}%`, x1 + 4, Math.min(y1, y2) + 14);
    });
    if (Number.isFinite(state.vcp.pivot)) {
      const y = b.y(state.vcp.pivot);
      ctx.strokeStyle = "rgba(227,182,77,.62)";
      ctx.setLineDash([2, 5]);
      ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(b.x(state.candles.length - 1) + 52, y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = COLORS.gold;
      ctx.fillText(`VCP pivot ${priceFmt(state.vcp.pivot)}`, b.pad.left + 8, y - 7);
    }
  }

  function drawVolume(ctx, b) {
    const vols = state.candles.map(c => c.volume);
    const maxVol = Math.max(...vols, 1);
    const cw = Math.max(2, b.innerW / Math.max(20, state.candles.length) * 0.68);
    state.candles.forEach((c, i) => {
      const x = b.x(i);
      const h = (c.volume / maxVol) * (b.volBottom - b.volTop);
      const up = c.close >= c.open;
      ctx.fillStyle = up ? "rgba(33,226,149,.34)" : "rgba(255,78,116,.34)";
      ctx.fillRect(x - cw / 2, b.volBottom - h, cw, Math.max(1, h));
    });
  }

  function drawCandles(ctx, b) {
    const cw = Math.max(2, Math.min(12, b.innerW / Math.max(20, state.candles.length) * 0.68));
    state.candles.forEach((c, i) => {
      const x = b.x(i);
      const yOpen = b.y(c.open), yClose = b.y(c.close), yHigh = b.y(c.high), yLow = b.y(c.low);
      const up = c.close >= c.open;
      ctx.strokeStyle = up ? COLORS.good : COLORS.bad;
      ctx.fillStyle = up ? COLORS.good : COLORS.bad;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, yHigh); ctx.lineTo(x, yLow); ctx.stroke();
      const top = Math.min(yOpen, yClose);
      const height = Math.max(1, Math.abs(yClose - yOpen));
      ctx.fillRect(x - cw / 2, top, cw, height);
    });
  }

  function drawEmaLine(ctx, b, values, color, label) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    let started = false, lastX = 0, lastY = 0;
    values.forEach((v, i) => {
      if (!Number.isFinite(v)) return;
      const x = b.x(i), y = b.y(v);
      if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
      lastX = x; lastY = y;
    });
    if (started) {
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.font = "11px Inter, sans-serif";
      ctx.fillText(label, lastX + 5, lastY - 4);
    }
  }
  function drawEMAs(ctx, b) {
    if (!state.layers.emas) return;
    drawEmaLine(ctx, b, state.indicators.ema20 || [], COLORS.gold, "EMA20");
    drawEmaLine(ctx, b, state.indicators.ema50 || [], COLORS.purple, "EMA50");
    drawEmaLine(ctx, b, state.indicators.ema200 || [], COLORS.cyan, "EMA120");
  }

  function bracketGeometry() {
    const br = state.bracket;
    if (!br) return null;
    const side = br.side;
    const risk = side === "long" ? br.entry - br.stop : br.stop - br.entry;
    const reward1 = side === "long" ? br.tp1 - br.entry : br.entry - br.tp1;
    const reward2 = side === "long" ? br.tp2 - br.entry : br.entry - br.tp2;
    return { risk, reward1, reward2, valid: risk > 0 && reward1 > 0 && reward2 > 0 };
  }

  function drawBracket(ctx, b, width) {
    const br = state.bracket;
    if (!br) return;
    const x0 = b.x(Math.max(0, br.startIndex ?? state.candles.length - 60));
    const x1 = Math.min(width - b.pad.right + 54, b.x(state.candles.length - 1) + 54);
    const yEntry = b.y(br.entry), yStop = b.y(br.stop), yTp1 = b.y(br.tp1), yTp2 = b.y(br.tp2);
    const riskTop = Math.min(yEntry, yStop), riskH = Math.abs(yStop - yEntry);
    const rewardTop = Math.min(yEntry, yTp2), rewardH = Math.abs(yTp2 - yEntry);
    ctx.fillStyle = COLORS.badSoft;
    ctx.fillRect(x0, riskTop, x1 - x0, riskH);
    ctx.fillStyle = COLORS.goodSoft;
    ctx.fillRect(x0, rewardTop, x1 - x0, rewardH);
    ctx.strokeStyle = "rgba(255,255,255,.16)";
    ctx.strokeRect(x0, riskTop, x1 - x0, riskH);
    ctx.strokeRect(x0, rewardTop, x1 - x0, rewardH);
    drawPriceLine(ctx, b, br.entry, COLORS.gold, "ENTRY", width, true);
    drawPriceLine(ctx, b, br.stop, COLORS.bad, "SL", width, true);
    drawPriceLine(ctx, b, br.tp1, COLORS.good, "TP1", width, true);
    drawPriceLine(ctx, b, br.tp2, COLORS.good, "TP2", width, true, 0.7);
    if (Number.isFinite(state.plan?.liquidation)) {
      drawPriceLine(ctx, b, state.plan.liquidation, "#ff7a33", "LIQ est", width, false, 0.9, [3, 6]);
    }
  }

  function drawPriceLine(ctx, b, price, color, label, width, handle = false, alpha = 1, dash = null) {
    const y = b.y(price);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 1.5;
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(width - b.pad.right + 68, y); ctx.stroke();
    ctx.setLineDash([]);
    const tag = `${label} ${priceFmt(price)}`;
    ctx.font = "11px Inter, sans-serif";
    const tw = ctx.measureText(tag).width + 14;
    const tx = width - b.pad.right + 70;
    ctx.globalAlpha = 1;
    ctx.fillStyle = color;
    roundRect(ctx, tx, y - 13, tw, 25, 8);
    ctx.fill();
    ctx.fillStyle = label === "ENTRY" ? "#120b05" : "#fff";
    ctx.fillText(tag, tx + 7, y + 4);
    if (handle) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(width - b.pad.right + 58, y, 5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
  }

  function drawDrawings(ctx, b) {
    const all = state.tempDrawing ? [...state.drawings, state.tempDrawing] : state.drawings;
    all.forEach((d, idx) => {
      const temp = d === state.tempDrawing;
      ctx.save();
      ctx.lineWidth = temp ? 1.3 : 1.8;
      ctx.strokeStyle = temp ? "rgba(255,214,111,.82)" : d.color || "rgba(255,214,111,.7)";
      ctx.fillStyle = d.fill || "rgba(156,103,255,.12)";
      if (d.type === "trend") {
        ctx.beginPath(); ctx.moveTo(b.x(d.a.index), b.y(d.a.price)); ctx.lineTo(b.x(d.b.index), b.y(d.b.price)); ctx.stroke();
        drawNode(ctx, b.x(d.a.index), b.y(d.a.price)); drawNode(ctx, b.x(d.b.index), b.y(d.b.price));
      } else if (d.type === "hline") {
        const y = b.y(d.price);
        ctx.setLineDash([10, 6]);
        ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(b.x(state.candles.length - 1) + 60, y); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = COLORS.gold;
        ctx.font = "11px Inter, sans-serif";
        ctx.fillText(d.label || `Line ${idx + 1} ${priceFmt(d.price)}`, b.pad.left + 8, y - 5);
      } else if (d.type === "zone") {
        const x1 = b.x(d.a.index), x2 = b.x(d.b.index), y1 = b.y(d.a.price), y2 = b.y(d.b.price);
        const x = Math.min(x1, x2), y = Math.min(y1, y2), w = Math.abs(x2 - x1), h = Math.abs(y2 - y1);
        ctx.fillRect(x, y, w, h);
        ctx.strokeRect(x, y, w, h);
      }
      ctx.restore();
    });
  }
  function drawNode(ctx, x, y) {
    ctx.fillStyle = COLORS.gold;
    ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill();
  }

  function drawMAE(ctx, b, width) {
    if (!state.layers.mae || !state.plan?.maeMfe || !state.bracket) return;
    const mae = state.plan.maeMfe.mae;
    if (!Number.isFinite(mae) || mae <= 0) return;
    const br = state.bracket;
    const price = br.side === "long" ? br.entry - mae : br.entry + mae;
    const y = b.y(price);
    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,.72)";
    ctx.setLineDash([2, 4]);
    ctx.beginPath(); ctx.moveTo(b.x(br.startIndex || 0), y); ctx.lineTo(width - b.pad.right + 62, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(255,255,255,.84)";
    ctx.font = "12px Inter, sans-serif";
    ctx.fillText(`MAE ${priceFmt(price)}`, b.pad.left + 8, y - 7);
    ctx.restore();
  }

  function drawHover(ctx, b, width, height) {
    if (!state.hover) return;
    const { x, y, index, price } = state.hover;
    if (x < b.pad.left || x > width - b.pad.right + 70 || y < b.pad.top || y > b.priceBottom) return;
    ctx.save();
    ctx.strokeStyle = "rgba(245,240,255,.28)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(x, b.pad.top); ctx.lineTo(x, b.volBottom); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(b.pad.left, y); ctx.lineTo(width - b.pad.right + 70, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(245,240,255,.86)";
    ctx.font = "11px Inter, sans-serif";
    ctx.fillText(priceFmt(price), width - b.pad.right + 82, y - 6);
    const c = state.candles[index];
    if (c) {
      ctx.fillText(c.time, x - 18, height - 9);
    }
    ctx.restore();
  }

  function renderChart() {
    const canvas = $("#chartCanvas");
    if (!canvas || !state.candles.length) return;
    const { ctx, width, height } = setupCanvas(canvas);
    const b = chartBounds(canvas);
    canvas._bounds = b;
    drawGrid(ctx, b, width, height);
    drawHeat(ctx, b, width);
    drawSupportResistance(ctx, b, width);
    drawVCP(ctx, b);
    drawBracket(ctx, b, width);
    drawVolume(ctx, b);
    drawCandles(ctx, b);
    drawEMAs(ctx, b);
    drawDrawings(ctx, b);
    drawMAE(ctx, b, width);
    drawHover(ctx, b, width, height);
  }

  function nearestBracketHandle(x, y) {
    const canvas = $("#chartCanvas");
    const b = canvas._bounds;
    if (!b || !state.bracket) return null;
    const handles = ["entry", "stop", "tp1", "tp2"];
    for (const key of handles) {
      const yy = b.y(state.bracket[key]);
      if (Math.abs(y - yy) <= 10 && x >= b.pad.left && x <= b.rect.width - b.pad.right + 74) return key;
    }
    return null;
  }

  function setTool(tool) {
    state.activeTool = tool;
    $$(".tool-btn[data-tool]").forEach(btn => btn.classList.toggle("active", btn.dataset.tool === tool));
    const canvas = $("#chartCanvas");
    canvas.style.cursor = tool === "cursor" ? "crosshair" : tool === "eraser" ? "not-allowed" : "copy";
  }

  function setBracket(side, entry, stop = null, tp1 = null, tp2 = null, startIndex = null) {
    const atr = state.atr || entry * 0.01;
    const risk = Math.max(atr * 1.15, entry * 0.0035);
    if (side === "long") {
      stop ??= entry - risk;
      tp1 ??= entry + risk * 2.05;
      tp2 ??= entry + risk * 3.1;
    } else {
      stop ??= entry + risk;
      tp1 ??= entry - risk * 2.05;
      tp2 ??= entry - risk * 3.1;
    }
    state.bracket = { side, entry, stop, tp1, tp2, startIndex: startIndex ?? Math.max(0, state.candles.length - 52) };
    $("#sideInput").value = side;
    syncInputsFromBracket();
    updateAll({ keepChart: true });
  }

  function syncInputsFromBracket() {
    if (!state.bracket) return;
    $("#entryInput").value = round(state.bracket.entry, 6);
    $("#stopInput").value = round(state.bracket.stop, 6);
    $("#tp1Input").value = round(state.bracket.tp1, 6);
    $("#tp2Input").value = round(state.bracket.tp2, 6);
    $("#sideInput").value = state.bracket.side;
  }

  function applyInputsToBracket() {
    const side = $("#sideInput").value;
    const entry = safeNumber($("#entryInput").value, NaN);
    const stop = safeNumber($("#stopInput").value, NaN);
    const tp1 = safeNumber($("#tp1Input").value, NaN);
    const tp2 = safeNumber($("#tp2Input").value, NaN);
    if (![entry, stop, tp1, tp2].every(Number.isFinite)) {
      toast("Entry, Stop, TP1, and TP2 must all be valid numbers.");
      return;
    }
    state.bracket = { side, entry, stop, tp1, tp2, startIndex: state.bracket?.startIndex ?? Math.max(0, state.candles.length - 52) };
    updateAll({ keepChart: true });
  }

  function autoSafeBracket() {
    const last = state.candles.at(-1);
    if (!last) return;
    const ema20 = lastNonNull(state.indicators.ema20, last.close);
    const ema50 = lastNonNull(state.indicators.ema50, last.close);
    const side = ema20 >= ema50 ? "long" : "short";
    const entry = last.close;
    const atr = state.atr || entry * 0.008;
    let stop, tp1, tp2;
    if (side === "long") {
      const support = state.supports.filter(l => l.kind === "support" && l.price < entry).sort((a, b) => b.price - a.price)[0];
      stop = support ? Math.min(support.zoneLow - atr * 0.16, entry - atr * 0.9) : entry - atr * 1.25;
      const risk = entry - stop;
      const resistance = state.supports.filter(l => l.kind === "resistance" && l.price > entry + risk * 1.6).sort((a, b) => a.price - b.price)[0];
      tp1 = resistance ? Math.max(resistance.price, entry + risk * 2.05) : entry + risk * 2.15;
      tp2 = entry + risk * 3.1;
    } else {
      const resistance = state.supports.filter(l => l.kind === "resistance" && l.price > entry).sort((a, b) => a.price - b.price)[0];
      stop = resistance ? Math.max(resistance.zoneHigh + atr * 0.16, entry + atr * 0.9) : entry + atr * 1.25;
      const risk = stop - entry;
      const support = state.supports.filter(l => l.kind === "support" && l.price < entry - risk * 1.6).sort((a, b) => b.price - a.price)[0];
      tp1 = support ? Math.min(support.price, entry - risk * 2.05) : entry - risk * 2.15;
      tp2 = entry - risk * 3.1;
    }
    setBracket(side, entry, stop, tp1, tp2, Math.max(0, state.candles.length - 1));
    toast(`Auto-safe ${side} bracket created from last close.`);
  }

  function computeMAEMFE(br, riskDistance) {
    if (!br || !Number.isFinite(riskDistance) || riskDistance <= 0) return null;
    const start = clamp(br.startIndex ?? Math.max(0, state.candles.length - 50), 0, state.candles.length - 1);
    let mae = 0, mfe = 0, outcome = "open";
    for (let i = start; i < state.candles.length; i++) {
      const c = state.candles[i];
      if (br.side === "long") {
        mae = Math.max(mae, br.entry - c.low);
        mfe = Math.max(mfe, c.high - br.entry);
        if (outcome === "open" && c.low <= br.stop) outcome = "stop touched";
        if (outcome === "open" && c.high >= br.tp1) outcome = "TP1 touched";
      } else {
        mae = Math.max(mae, c.high - br.entry);
        mfe = Math.max(mfe, br.entry - c.low);
        if (outcome === "open" && c.high >= br.stop) outcome = "stop touched";
        if (outcome === "open" && c.low <= br.tp1) outcome = "TP1 touched";
      }
    }
    return { mae, mfe, maeR: mae / riskDistance, mfeR: mfe / riskDistance, outcome };
  }

  function nearestInvalidation(side, entry) {
    if (side === "long") return state.supports.filter(l => l.kind === "support" && l.price < entry).sort((a, b) => b.price - a.price)[0] || null;
    return state.supports.filter(l => l.kind === "resistance" && l.price > entry).sort((a, b) => a.price - b.price)[0] || null;
  }

  function calculatePlan() {
    const br = state.bracket;
    if (!br) return null;
    const geom = bracketGeometry();
    const equity = safeNumber($("#equityInput").value, 10000);
    const riskPct = safeNumber($("#riskPctInput").value, 1);
    const leverage = Math.max(1, safeNumber($("#leverageInput").value, 3));
    const feeBps = Math.max(0, safeNumber($("#feeBpsInput").value, 6));
    const style = $("#orderStyleInput").value;
    const riskDollars = equity * riskPct / 100;
    const riskDistance = Math.abs(geom?.risk || NaN);
    const reward1 = geom?.reward1;
    const reward2 = geom?.reward2;
    const rr1 = riskDistance > 0 ? reward1 / riskDistance : NaN;
    const rr2 = riskDistance > 0 ? reward2 / riskDistance : NaN;
    const qty = riskDistance > 0 ? riskDollars / riskDistance : NaN;
    const notional = qty * br.entry;
    const fees = notional * feeBps / 10000 * 2;
    const initialMargin = notional / leverage;
    const mmr = 0.005;
    const liquidation = br.side === "long" ? br.entry * (1 - 1 / leverage + mmr) : br.entry * (1 + 1 / leverage - mmr);
    const liqBuffer = br.side === "long" ? (br.stop - liquidation) / br.entry * 100 : (liquidation - br.stop) / br.entry * 100;
    const stopAtr = riskDistance / Math.max(1e-9, state.atr || riskDistance);
    const invalidation = nearestInvalidation(br.side, br.entry);
    const maeMfe = computeMAEMFE(br, riskDistance);
    const guards = buildGuardrails({ br, geom, equity, riskPct, leverage, riskDistance, reward1, reward2, rr1, rr2, qty, notional, fees, initialMargin, liquidation, liqBuffer, stopAtr, invalidation, maeMfe, style });
    const fails = guards.filter(g => g.status === "fail").length;
    const warns = guards.filter(g => g.status === "warn").length;
    const score = clamp(Math.round(100 - fails * 18 - warns * 7 - Math.max(0, riskPct - 1) * 5 - Math.max(0, leverage - 5) * 2), 0, 100);
    return { symbol: currentSymbol(), timeframe: currentTimeframe(), mode: "broker-routed", side: br.side, orderStyle: style, entry: br.entry, stopLoss: br.stop, takeProfit: [br.tp1, br.tp2], rr1, rr2, riskDistance, equity, riskPct, maxLossUsd: riskDollars, qty, notional, fees, initialMargin, leverage, liquidation, liqBuffer, stopAtr, invalidation, maeMfe, guards, score, edge: state.edge ? { symbol: state.edge.symbol, regime: state.edge.regime, risk_score: state.edge.risk_score, support: state.edge.support, resistance: state.edge.resistance } : null, vcp: state.vcp, drawings: state.drawings };
  }

  function buildGuardrails(ctx) {
    const g = [];
    const add = (status, title, detail) => g.push({ status, title, detail });
    const geometryGood = ctx.geom?.valid;
    add(geometryGood ? "pass" : "fail", "Bracket geometry", geometryGood ? "Entry, stop, and targets are on the correct side for the selected direction." : "Stop and targets must be placed on opposite sides of entry before any signal is usable.");
    if (Number.isFinite(ctx.rr1)) add(ctx.rr1 >= 2 ? "pass" : ctx.rr1 >= 1.4 ? "warn" : "fail", "Reward:risk", `TP1 is ${ctx.rr1.toFixed(2)}R. Safety profile prefers 2R or better for volatile futures.`);
    else add("fail", "Reward:risk", "Cannot compute R:R until bracket geometry is valid.");
    add(ctx.riskPct <= 1 ? "pass" : ctx.riskPct <= 2 ? "warn" : "fail", "Account risk cap", `Risk is ${ctx.riskPct.toFixed(2)}% of equity (${money(ctx.equity * ctx.riskPct / 100)}).`);
    if (Number.isFinite(ctx.stopAtr)) add(ctx.stopAtr >= 0.7 && ctx.stopAtr <= 3.5 ? "pass" : ctx.stopAtr < 0.7 ? "warn" : "warn", "ATR stop distance", `Stop is ${ctx.stopAtr.toFixed(2)}× ATR. Very tight stops can be clipped by normal crypto noise.`);
    add(ctx.leverage <= 5 ? "pass" : ctx.leverage <= 10 ? "warn" : "fail", "Leverage governor", `${ctx.leverage.toFixed(1)}× leverage selected. Conservative mode prefers 5× or lower.`);
    add(ctx.liqBuffer > 0.75 ? "pass" : ctx.liqBuffer > 0 ? "warn" : "fail", "Liquidation before stop", ctx.liqBuffer > 0 ? `Estimated liquidation is ${pct(ctx.liqBuffer)} beyond the stop.` : "Estimated liquidation can occur before the stop. Reduce leverage or move/resize the trade.");
    if (ctx.invalidation) {
      const beyond = ctx.br.side === "long" ? ctx.br.stop <= ctx.invalidation.zoneLow : ctx.br.stop >= ctx.invalidation.zoneHigh;
      add(beyond ? "pass" : "warn", "Structure invalidation", beyond ? `Stop is beyond nearest ${ctx.invalidation.kind} zone at ${priceFmt(ctx.invalidation.price)}.` : `Stop is inside/near ${ctx.invalidation.kind} zone at ${priceFmt(ctx.invalidation.price)}; consider placing it beyond invalidation.`);
    } else add("warn", "Structure invalidation", "No nearby support/resistance cluster found; validate manually with drawn lines.");
    if (ctx.style === "limit_retest") add("warn", "Limit retest style", "Better entry/R:R is possible, but the trade may be missed if price never pulls back.");
    if (ctx.style === "market_confirmation") add("warn", "Market confirmation style", "Higher fill probability, but slippage and lower R:R are more likely during fast candles.");
    if (ctx.style === "stop_breakout") add("warn", "Stop breakout style", "Breakout confirmation can work, but wicks through pivots need extra slippage buffer.");
    if (state.vcp?.score >= 55) {
      const pivotOk = ctx.br.side === "long" ? ctx.br.entry >= state.vcp.pivot * 0.992 : true;
      add(pivotOk ? "pass" : "warn", "VCP pivot gate", `VCP score ${state.vcp.score.toFixed(0)}. ${pivotOk ? "Entry is close to/above pivot." : "Wait for pivot confirmation or a planned retest."}`);
    } else add("warn", "VCP pivot gate", `VCP score ${state.vcp?.score?.toFixed(0) ?? "--"}; no clean contraction edge yet.`);
    if (ctx.maeMfe) {
      add(ctx.maeMfe.maeR < 0.8 ? "pass" : ctx.maeMfe.maeR < 1 ? "warn" : "fail", "Historical MAE replay", `Since the bracket start, MAE reached ${ctx.maeMfe.maeR.toFixed(2)}R and MFE reached ${ctx.maeMfe.mfeR.toFixed(2)}R (${ctx.maeMfe.outcome}).`);
    }
    return g;
  }

  function updatePlanUI() {
    state.plan = calculatePlan();
    const plan = state.plan;
    const last = state.candles.at(-1);
    $("#priceNow").textContent = last ? priceFmt(last.close) : "--";
    $("#priceSub").textContent = state.edge ? `${state.edge.symbol} · ${state.edge.regime}` : `${currentSymbol()} · ${currentTimeframe()}`;
    $("#chartTitle").textContent = `${currentSymbol()} · ${currentTimeframe()}`;
    if (!plan) {
      $("#safetyScore").textContent = "--";
      $("#scoreText").textContent = "Draw a bracket";
      $("#rrValue").textContent = "--";
      $("#rrSub").textContent = "No active plan";
      $("#liqBuffer").textContent = "--";
      $("#liqSub").textContent = "No active plan";
      $("#guardList").innerHTML = `<div class="guard-item warn"><div class="guard-icon">!</div><div><b>No bracket yet</b><p>Create a Long/Short TP/SL bracket on the chart or press Auto-safe bracket.</p></div></div>`;
      $("#guardSummary").textContent = "waiting";
      $("#planMetrics").innerHTML = "";
      $("#planJson").textContent = "{}";
      updateMaeUI(null);
      return;
    }
    $("#safetyScore").textContent = `${plan.score}`;
    $("#scoreText").textContent = plan.score >= 80 ? "Plan looks disciplined" : plan.score >= 60 ? "Needs review" : "Unsafe / gated";
    $("#scoreCard").classList.toggle("bad", plan.score < 60);
    $("#scoreCard").classList.toggle("warn", plan.score >= 60 && plan.score < 80);
    $("#scoreCard").classList.toggle("good", plan.score >= 80);
    $("#rrValue").textContent = Number.isFinite(plan.rr1) ? `${plan.rr1.toFixed(2)}R` : "--";
    $("#rrSub").textContent = Number.isFinite(plan.rr2) ? `TP2 ${plan.rr2.toFixed(2)}R` : "Check target";
    $("#liqBuffer").textContent = Number.isFinite(plan.liqBuffer) ? pct(plan.liqBuffer) : "--";
    $("#liqSub").textContent = `Est. liq ${priceFmt(plan.liquidation)}`;
    const pass = plan.guards.filter(x => x.status === "pass").length;
    const warn = plan.guards.filter(x => x.status === "warn").length;
    const fail = plan.guards.filter(x => x.status === "fail").length;
    $("#guardSummary").textContent = `${pass} pass · ${warn} warn · ${fail} fail`;
    $("#guardList").innerHTML = plan.guards.map(item => `<div class="guard-item ${item.status}"><div class="guard-icon">${item.status === "pass" ? "✓" : item.status === "warn" ? "!" : "×"}</div><div><b>${escapeHtml(item.title)}</b><p>${escapeHtml(item.detail)}</p></div></div>`).join("");
    $("#planMetrics").innerHTML = [
      metric("Max loss", money(plan.maxLossUsd), plan.maxLossUsd <= plan.equity * 0.01 ? "good" : "warn"),
      metric("Position qty", qtyFmt(plan.qty), ""),
      metric("Notional", money(plan.notional), plan.notional / plan.equity > 5 ? "warn" : ""),
      metric("Initial margin", money(plan.initialMargin), ""),
      metric("Fees est.", money(plan.fees), ""),
      metric("Stop × ATR", Number.isFinite(plan.stopAtr) ? `${plan.stopAtr.toFixed(2)}×` : "--", plan.stopAtr < 0.7 ? "warn" : "good"),
    ].join("");
    $("#planJson").textContent = JSON.stringify(exportablePlan(), null, 2);
    updateMaeUI(plan.maeMfe);
  }

  function metric(label, value, tone) { return `<div class="metric-tile ${tone || ""}"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b></div>`; }
  function escapeHtml(value) { return String(value).replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch])); }

  function updateMaeUI(mae) {
    if (!mae) {
      $("#maeState").textContent = "needs bracket";
      $("#maeMeter").value = 0; $("#mfeMeter").value = 0; $("#survivalMeter").value = 0;
      $("#maeValue").textContent = "--"; $("#mfeValue").textContent = "--"; $("#survivalValue").textContent = "--";
      return;
    }
    $("#maeState").textContent = mae.outcome;
    $("#maeMeter").value = clamp(mae.maeR * 100, 0, 100);
    $("#mfeMeter").value = clamp(mae.mfeR * 50, 0, 100);
    $("#survivalMeter").value = clamp((1 - mae.maeR) * 100, 0, 100);
    $("#maeValue").textContent = `${mae.maeR.toFixed(2)}R`;
    $("#mfeValue").textContent = `${mae.mfeR.toFixed(2)}R`;
    $("#survivalValue").textContent = mae.maeR < 1 ? `${((1 - mae.maeR) * 100).toFixed(0)}%` : "breached";
  }

  function updatePatternUI() {
    const v = state.vcp;
    $("#vcpScore").textContent = v ? `${Math.round(v.score)}` : "--";
    $("#vcpSub").textContent = v ? v.status : "No scan";
    $("#patternSummary").textContent = v ? `${Math.round(v.score)} / 100` : "auto";
    const bars = (v?.contractions || []).slice(-4).map(c => `<div class="contraction-bar" style="height:${clamp(c.pct * 4, 8, 42)}px"><span>${c.pct.toFixed(1)}%</span></div>`).join("");
    $("#patternBody").innerHTML = `
      <div class="pattern-pill"><b><span>${escapeHtml(v?.status || "Scanning")}</span><span>${Math.round(v?.score || 0)}</span></b><p>Contractions shrink: ${v?.shrink || 0}. Volume dry-up checks: ${v?.volDry || 0}. Pivot: ${priceFmt(v?.pivot)}. Final contraction low: ${priceFmt(v?.finalLow)}.</p></div>
      <div class="pattern-pill"><b><span>Contraction map</span><span>${(v?.contractions || []).length} legs</span></b><div class="contractions">${bars || "<p>No clean high-to-low contraction sequence yet.</p>"}</div></div>
      <div class="pattern-pill"><b><span>Safety interpretation</span><span>VCP</span></b><p>A long breakout plan should wait for pivot confirmation or a clean retest. Stop placement belongs under the final contraction low or a stronger invalidation zone, not inside normal noise.</p></div>
    `;
  }

  function updateTickerStrip() {
    const last = state.candles.at(-1);
    const prev = state.candles.at(-8)?.close || state.candles.at(-2)?.close || last?.close;
    const change = last && prev ? (last.close - prev) / prev * 100 : 0;
    const tickers = [
      { s: currentSymbol(), p: last?.close, ch: change },
      { s: "ATR", p: state.atr, ch: null },
      { s: "VCP", p: state.vcp?.score, ch: null },
      { s: "Risk", p: state.plan?.score, ch: null },
      { s: state.edge?.symbol || "EDGE", p: state.edge?.risk_score, ch: null },
    ];
    $("#tickerStrip").innerHTML = tickers.map(t => `<div class="ticker ${t.ch >= 0 ? "up" : "down"}"><b>${escapeHtml(t.s)}</b><span>${t.ch === null ? priceFmt(t.p) : `${priceFmt(t.p)} · ${t.ch >= 0 ? "+" : ""}${t.ch.toFixed(2)}%`}</span></div>`).join("");
  }

  function exportablePlan() {
    const p = state.plan;
    if (!p) return {};
    return {
      symbol: p.symbol,
      timeframe: p.timeframe,
      mode: p.mode,
      side: p.side,
      order_style: p.orderStyle,
      entry: round(p.entry, 8),
      stop_loss: round(p.stopLoss, 8),
      take_profit: p.takeProfit.map(x => round(x, 8)),
      reward_risk: { tp1_R: round(p.rr1, 4), tp2_R: round(p.rr2, 4) },
      risk: {
        equity: p.equity,
        risk_pct: p.riskPct,
        max_loss_usd: round(p.maxLossUsd, 2),
        position_qty: round(p.qty, 8),
        notional_usd: round(p.notional, 2),
        fee_estimate_usd: round(p.fees, 2),
        leverage: p.leverage,
        initial_margin_estimate_usd: round(p.initialMargin, 2),
        liquidation_estimate: round(p.liquidation, 8),
        liquidation_buffer_pct: round(p.liqBuffer, 4),
        stop_distance_atr: round(p.stopAtr, 4)
      },
      sentinel_score: p.score,
      guardrails: p.guards,
      vcp: p.vcp ? { score: round(p.vcp.score, 2), status: p.vcp.status, pivot: round(p.vcp.pivot, 8), final_low: round(p.vcp.finalLow, 8), contractions: p.vcp.contractions.map(c => ({ start_index: c.startIndex, end_index: c.endIndex, pullback_pct: round(c.pct, 4), avg_volume: round(c.volume, 2) })) } : null,
      edge_context: p.edge,
      drawings: p.drawings,
      operator_note: "Broker-routed TP/SL planning payload. Validate exchange-specific order semantics, slippage, funding, and liquidity before any live action."
    };
  }

  function updateAll({ keepChart = false } = {}) {
    if (!state.candles.length) return;
    computeIndicators();
    updatePlanUI();
    updatePatternUI();
    updateTickerStrip();
    renderBackendPanels();
    if (!keepChart) syncInputsFromBracket();
    renderChart();
  }

  function loadLive Data(scenario = $("#scenarioInput").value) {
    const bars = clamp(Math.round(safeNumber($("#barsInput").value, 180)), 80, 420);
    const symbol = rawSymbol(currentSymbol());
    state.edge = null;
    state.candles = generateCandles(symbol, bars, scenario);
    markCandleSeries(symbol, currentTimeframe(), "live-data");
    state.drawings = [];
    state.bracket = null;
    updateAll();
    syncMarkPriceFromChart();
    toast(`${titleCase(scenario)} market loaded.`);
  }

  function loadVCP() {
    $("#scenarioInput").value = "vcp";
    loadLive Data("vcp");
    autoSafeBracket();
    $("#orderStyleInput").value = "stop_breakout";
  }

  function loadEdge() {
    const packet = EDGE_HEATMAP_SAMPLE;
    state.edge = packet;
    setCurrentSymbol(packet.symbol || "SPY");
    $("#timeframeInput").value = "3m";
    state.candles = edgeToCandles(packet);
    markCandleSeries(packet.symbol || "SPY", "3m", "edge");
    state.drawings = [];
    state.bracket = null;
    updateAll();
    syncMarkPriceFromChart();
    toast(`Loaded Edge ${packet.mode} snapshot: ${packet.symbol} · ${packet.regime}.`);
  }

  function pointerPosition(event) {
    const rect = $("#chartCanvas").getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }
  function pointFromPointer(event) {
    const canvas = $("#chartCanvas");
    const b = canvas._bounds || chartBounds(canvas);
    const p = pointerPosition(event);
    return { ...p, index: b.indexAtX(p.x), price: b.priceAtY(p.y), bounds: b };
  }

  function onPointerDown(event) {
    if (state.locked && state.activeTool !== "cursor") {
      toast("Plan is locked. Unlock it before changing drawings or brackets.");
      return;
    }
    const canvas = $("#chartCanvas");
    canvas.setPointerCapture?.(event.pointerId);
    const pt = pointFromPointer(event);
    const handle = nearestBracketHandle(pt.x, pt.y);
    if (handle && !state.locked) {
      state.drag = { type: "bracket", key: handle };
      return;
    }
    if (state.activeTool === "cursor") return;
    if (state.activeTool === "eraser") {
      eraseNearest(pt);
      return;
    }
    if (state.activeTool === "long" || state.activeTool === "short") {
      setBracket(state.activeTool, pt.price, null, null, null, pt.index);
      toast(`${titleCase(state.activeTool)} bracket placed. Drag handles to refine.`);
      return;
    }
    if (state.activeTool === "horizontal") {
      state.drawings.push({ type: "hline", price: pt.price, label: `Manual line ${priceFmt(pt.price)}`, color: "rgba(255,214,111,.74)" });
      updateAll({ keepChart: true });
      scheduleDrawingPersist();
      return;
    }
    if (state.activeTool === "trend") {
      state.drag = { type: "drawing" };
      state.tempDrawing = { type: "trend", a: { index: pt.index, price: pt.price }, b: { index: pt.index, price: pt.price }, color: "rgba(255,214,111,.82)" };
    }
    if (state.activeTool === "zone") {
      state.drag = { type: "drawing" };
      state.tempDrawing = { type: "zone", a: { index: pt.index, price: pt.price }, b: { index: pt.index, price: pt.price }, fill: "rgba(156,103,255,.12)", color: "rgba(156,103,255,.62)" };
    }
  }

  function onPointerMove(event) {
    const pt = pointFromPointer(event);
    state.hover = { x: pt.x, y: pt.y, index: pt.index, price: pt.price };
    const c = state.candles[pt.index];
    if (c) $("#crosshairReadout").textContent = `${c.time} · O ${priceFmt(c.open)} H ${priceFmt(c.high)} L ${priceFmt(c.low)} C ${priceFmt(c.close)} · cursor ${priceFmt(pt.price)}`;
    if (state.drag?.type === "bracket" && state.bracket && !state.locked) {
      state.bracket[state.drag.key] = Math.max(0.00000001, pt.price);
      syncInputsFromBracket();
      updateAll({ keepChart: true });
      return;
    }
    if (state.drag?.type === "drawing" && state.tempDrawing) {
      state.tempDrawing.b = { index: pt.index, price: pt.price };
      renderChart();
      return;
    }
    renderChart();
  }

  function onPointerUp(event) {
    if (state.drag?.type === "drawing" && state.tempDrawing) {
      const d = state.tempDrawing;
      const enough = d.type === "zone" ? Math.abs(d.a.index - d.b.index) >= 2 && Math.abs(d.a.price - d.b.price) > (state.atr || 1) * 0.12 : Math.abs(d.a.index - d.b.index) >= 2 || Math.abs(d.a.price - d.b.price) > (state.atr || 1) * 0.1;
      if (enough) { state.drawings.push(d); scheduleDrawingPersist(); }
      state.tempDrawing = null;
      updateAll({ keepChart: true });
    }
    state.drag = null;
  }

  function eraseNearest(pt) {
    if (!state.drawings.length) return;
    const canvas = $("#chartCanvas");
    const b = canvas._bounds || chartBounds(canvas);
    let best = { idx: -1, dist: Infinity };
    state.drawings.forEach((d, idx) => {
      let dist = Infinity;
      if (d.type === "hline") dist = Math.abs(b.y(d.price) - pt.y);
      if (d.type === "trend") dist = distanceToSegment(pt.x, pt.y, b.x(d.a.index), b.y(d.a.price), b.x(d.b.index), b.y(d.b.price));
      if (d.type === "zone") {
        const x1 = b.x(d.a.index), x2 = b.x(d.b.index), y1 = b.y(d.a.price), y2 = b.y(d.b.price);
        const inside = pt.x >= Math.min(x1, x2) && pt.x <= Math.max(x1, x2) && pt.y >= Math.min(y1, y2) && pt.y <= Math.max(y1, y2);
        dist = inside ? 0 : Math.min(Math.abs(pt.x - x1), Math.abs(pt.x - x2), Math.abs(pt.y - y1), Math.abs(pt.y - y2));
      }
      if (dist < best.dist) best = { idx, dist };
    });
    if (best.idx >= 0 && best.dist < 22) {
      state.drawings.splice(best.idx, 1);
      updateAll({ keepChart: true });
      scheduleDrawingPersist();
      toast("Drawing removed.");
    }
  }
  function distanceToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1, dy = y2 - y1;
    if (dx === 0 && dy === 0) return Math.hypot(px - x1, py - y1);
    const t = clamp(((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy), 0, 1);
    return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
  }

  function parsePastedData(text) {
    const trimmed = text.trim();
    if (!trimmed) throw new Error("No data pasted.");
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
      const data = JSON.parse(trimmed);
      if (Array.isArray(data)) return normalizeCandles(data);
      if (Array.isArray(data.candles)) return normalizeCandles(data.candles);
      if (Array.isArray(data.series)) return edgeToCandles(data);
      throw new Error("JSON must be an array of candles, contain candles[], or contain Edge series[].");
    }
    const lines = trimmed.split(/\r?\n/).filter(Boolean);
    const header = lines[0].split(",").map(s => s.trim().toLowerCase());
    const idx = name => header.indexOf(name);
    const required = ["open", "high", "low", "close"].map(idx);
    if (required.some(i => i < 0)) throw new Error("CSV needs open,high,low,close columns.");
    return normalizeCandles(lines.slice(1).map(line => {
      const cols = line.split(",");
      return { time: cols[idx("time")] || cols[0], open: cols[idx("open")], high: cols[idx("high")], low: cols[idx("low")], close: cols[idx("close")], volume: idx("volume") >= 0 ? cols[idx("volume")] : 0 };
    }));
  }
  function normalizeCandles(items) {
    return items.map((c, i) => ({
      time: c.time ?? c.t ?? i,
      open: safeNumber(c.open ?? c.o, NaN),
      high: safeNumber(c.high ?? c.h, NaN),
      low: safeNumber(c.low ?? c.l, NaN),
      close: safeNumber(c.close ?? c.c, NaN),
      volume: safeNumber(c.volume ?? c.v, 0),
    })).filter(c => [c.open, c.high, c.low, c.close].every(Number.isFinite));
  }

  function copyText(text) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    return Promise.resolve();
  }

  function exportPlanFile() {
    const data = JSON.stringify(exportablePlan(), null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sentinel-guardian-plan-${currentSymbol()}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }



  // ---------------------------------------------------------------------------
  // Backend-wired Guardian operator extensions
  // ---------------------------------------------------------------------------
  function readLocalJson(key, fallback) {
    try {
      const raw = window.localStorage?.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  function writeLocalJson(key, value) {
    try { window.localStorage?.setItem(key, JSON.stringify(value)); } catch { /* noop */ }
  }

  async function api(path, options = {}) {
    const request = {
      method: options.method || "GET",
      credentials: "same-origin",
      headers: { ...(options.headers || {}) },
    };
    if (options.body !== undefined) {
      request.headers["Content-Type"] = "application/json";
      request.body = typeof options.body === "string" ? options.body : JSON.stringify(options.body);
    }
    const response = await fetch(path, request);
    const text = await response.text();
    let payload;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = text; }
    if (!response.ok) {
      const detail = typeof payload === "object" && payload !== null ? (payload.detail || payload.error || JSON.stringify(payload)) : payload;
      throw new Error(detail || `Request failed (${response.status})`);
    }
    return payload;
  }


  function wsUrl(path, params = {}) {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
    });
    return `${proto}//${window.location.host}${path}${query.toString() ? `?${query}` : ""}`;
  }

  function apiErrorMessage(err) { return err?.message || String(err || "unknown error"); }

  function normalizeIncomingCandles(value) {
    return safeArray(value).map(c => ({
      time: String(c.time || c.label || c.timestamp || c.open_time || ""),
      open: +c.open,
      high: +c.high,
      low: +c.low,
      close: +c.close,
      volume: +c.volume || +c.quoteVol || +c.baseVol || 0,
    })).filter(c => [c.open, c.high, c.low, c.close].every(Number.isFinite) && c.low <= c.high);
  }

  function upsertLiveCandle(candle) {
    const normalized = normalizeIncomingCandles([candle])[0];
    if (!normalized) return false;
    const last = state.candles[state.candles.length - 1];
    if (last && normalized.time && last.time === normalized.time) state.candles[state.candles.length - 1] = normalized;
    else state.candles.push(normalized);
    const maxBars = clamp(Math.round(safeNumber($("#barsInput")?.value, 180)), 80, 500);
    if (state.candles.length > maxBars) state.candles = state.candles.slice(-maxBars);
    state.edge = null;
    updateAll({ keepChart: true });
    return true;
  }

  function drawingSymbol() { return rawSymbol(currentSymbol()); }

  function setStatus(message, tone = "") {
    const line = $("#guardianStatusLine");
    if (line) {
      line.textContent = message;
      line.className = `status-line ${tone}`.trim();
    }
  }

  function setPill(id, value, tone = "") {
    const el = $("#" + id);
    if (!el) return;
    el.classList.remove("ok", "warn", "bad", "streaming");
    if (tone) el.classList.add(tone);
    const span = el.querySelector("span");
    if (span) span.textContent = value;
  }

  function safeArray(value) { return Array.isArray(value) ? value : []; }
  function objSize(value) { return value && typeof value === "object" ? Object.keys(value).length : 0; }
  function boolLabel(value) { return value ? "on" : "off"; }
  function compactId(value) {
    const raw = String(value || "");
    return raw.length > 14 ? `${raw.slice(0, 7)}…${raw.slice(-5)}` : raw || "—";
  }
  function isoOrNow(value) {
    try { return value ? new Date(value).toLocaleString() : new Date().toLocaleString(); } catch { return String(value || "—"); }
  }
  function jsonBlock(value) { return JSON.stringify(value ?? {}, null, 2); }
  function setJson(id, value) { const el = $("#" + id); if (el) el.textContent = jsonBlock(value); }
  function downloadText(filename, content, type = "application/json") {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }
  function strategyTitle(value) { return titleCase(String(value || "manual").replaceAll("-", "_")); }
  function rawSymbol(value) { return String(value || "BTCUSDT").replace("/", "").toUpperCase(); }

  function activeData() { return state.backend.data || {}; }
  function activeOrders() { return safeArray(activeData().orders); }
  function activePositions() { return safeArray(activeData().positions); }
  function activeSignals() { return safeArray(activeData().signals); }
  function activeApprovals() { return safeArray(activeData().approvals); }
  function activeAudit() { return safeArray(activeData().audit); }

  function renderBackendPanels() {
    renderGlobalStatus();
    renderDashboardPanel();
    renderSignalsPanel();
    renderDeskPanel();
    renderRiskPanel();
    renderVcpPanel();
    renderDrawingsPanel();
    renderPortfolioPanel();
    renderStrategiesPanel();
    renderExchangesPanel();
    renderWarRoomPanel();
    renderAuditPanel();
    renderDataPanel();
  }

  async function refreshBackendState(showToast = false) {
    setStatus("Refreshing Sentinel Chain API state…");
    try {
      const data = await api("/ui/state");
      state.backend.data = data;
      const calls = await Promise.allSettled([
        api("/exchanges"),
        api("/exchanges/platforms"),
        api("/strategy-presets"),
        api("/brackets"),
        api("/brackets/health"),
        api("/brackets/risk-summary"),
        api("/brackets/coverage"),
        api("/war-room/features"),
        api("/audit"),
        api("/guardian/live/status"),
        api(`/guardian/edge/latest?symbol=${encodeURIComponent(drawingSymbol())}`),
        api(`/guardian/drawings?symbol=${encodeURIComponent(drawingSymbol())}`),
      ]);
      const [exchanges, platforms, strategies, brackets, health, risk, coverage, warFeatures, audit, liveStatus, edgeLatest, serverDrawings] = calls;
      if (exchanges.status === "fulfilled") state.backend.exchanges = exchanges.value.exchanges || [];
      if (platforms.status === "fulfilled") state.backend.platforms = platforms.value.platforms || [];
      if (strategies.status === "fulfilled") state.backend.strategies = strategies.value.presets || [];
      if (brackets.status === "fulfilled") state.backend.brackets = brackets.value.brackets || [];
      if (health.status === "fulfilled") state.backend.bracketHealth = health.value.health || health.value;
      if (risk.status === "fulfilled") state.backend.bracketRisk = risk.value.summary || risk.value;
      if (coverage.status === "fulfilled") state.backend.coverage = coverage.value;
      if (warFeatures.status === "fulfilled") state.backend.warFeatures = warFeatures.value;
      if (audit.status === "fulfilled" && state.backend.data) state.backend.data.audit = audit.value.events || state.backend.data.audit || [];
      if (liveStatus.status === "fulfilled") state.backend.liveStatus = liveStatus.value;
      if (edgeLatest.status === "fulfilled") state.backend.edgeLatest = edgeLatest.value;
      if (serverDrawings.status === "fulfilled") state.backend.serverDrawings = serverDrawings.value;
      renderBackendPanels();
      setStatus("Sentinel Chain API state refreshed.", "ok");
      if (showToast) toast("Backend state refreshed.");
    } catch (err) {
      setStatus(`Unable to load Sentinel Chain API state: ${err.message || err}`, "error");
      setPill("apiStatePill", "error", "bad");
      if (showToast) toast(err.message || String(err));
    }
  }

  function renderGlobalStatus() {
    const data = activeData();
    const halted = Boolean(data.control?.halted || data.health?.halted);
    setPill("apiStatePill", state.backend.data ? "connected" : "offline", state.backend.data ? "ok" : "warn");
    setPill("brokerStatePill", halted ? "halted" : "armed", halted ? "bad" : "ok");
    setPill("approvalStatePill", data.execution?.require_approval ? `${activeApprovals().length} queued` : "broker direct", data.execution?.require_approval ? "warn" : "ok");
    const liveStatus = state.backend.liveStatus || data.live || {};
    const bitunixLive = Boolean(liveStatus.bitunix?.live_execution_enabled);
    setPill("liveLockPill", bitunixLive ? "armed" : "locked", "warn");
    setPill("edgeStreamPill", state.backend.edgeConnected ? `${state.backend.edgeEventCount} events` : "offline", state.backend.edgeConnected ? "streaming" : "warn");
    setPill("candleStreamPill", state.backend.candleConnected ? `${state.backend.candleEventCount} ticks` : "idle", state.backend.candleConnected ? "streaming" : "warn");
    const haltBtn = $("#haltBtn"); if (haltBtn) haltBtn.disabled = halted;
    const resumeBtn = $("#resumeBtn"); if (resumeBtn) resumeBtn.disabled = !halted;
  }

  function opsKpi(label, value, sub = "", tone = "") {
    return `<div class="ops-kpi ${tone}"><span>${escapeHtml(label)}</span><b>${escapeHtml(value)}</b><em>${escapeHtml(sub)}</em></div>`;
  }

  function compactRow(title, detail, chips = []) {
    const meta = chips.length ? `<div class="meta">${chips.map(c => `<span class="chip ${c.tone || ""}">${escapeHtml(c.label)}</span>`).join("")}</div>` : "";
    return `<div class="compact-row"><b>${escapeHtml(title)}</b><p>${escapeHtml(detail)}</p>${meta}</div>`;
  }

  function renderDashboardPanel() {
    const data = activeData();
    const orders = activeOrders();
    const positions = activePositions();
    const signals = activeSignals();
    const approvals = activeApprovals();
    const audit = activeAudit();
    const account = data.account || {};
    const halted = Boolean(data.control?.halted);
    const kpis = $("#dashboardKpis");
    if (kpis) {
      kpis.innerHTML = [
        opsKpi("Engine", halted ? "Halted" : "Armed", data.control?.reason || "broker engine", halted ? "bad" : "good"),
        opsKpi("Equity", money(safeNumber(account.equity)), `Daily P&L ${money(safeNumber(account.daily_pnl))}`, "purple"),
        opsKpi("Open Notional", money(safeNumber(account.open_notional)), `${positions.length} positions`, safeNumber(account.open_notional) ? "warn" : "good"),
        opsKpi("Inbox", String(signals.length), `${approvals.length} approvals`, approvals.length ? "warn" : "good"),
      ].join("");
    }
    const ts = $("#dashboardTimestamp"); if (ts) ts.textContent = new Date().toLocaleTimeString();
    const snap = $("#operatorSnapshot");
    if (snap) {
      snap.innerHTML = [
        compactRow("Mode pills", `Webhook ${halted ? "halted" : "live"} · approvals ${boolLabel(data.execution?.require_approval)} · broker fills ${data.execution?.submit_intent || "broker_order"}`),
        compactRow("Risk state ring", `Max order ${money(safeNumber(data.risk?.max_order_notional))} · max daily loss ${money(safeNumber(data.risk?.max_daily_loss))} · open risk ${money(safeNumber(account.open_risk_amount))}`),
        compactRow("Exchange fabric", `${state.backend.exchanges.length} venues · ${state.backend.platforms.length} platform adapters visible`),
        compactRow("Protections", `${safeArray(data.protections?.rules).length || objSize(data.protections)} runtime protection entries loaded`),
      ].join("");
    }
    const inbox = $("#dashboardSignals");
    if (inbox) {
      const recent = signals.slice(-5).reverse();
      inbox.innerHTML = recent.length ? recent.map(s => compactRow(`${s.symbol || "—"} ${String(s.side || "").toUpperCase()}`, `ID ${compactId(s.signal_id)} · ${s.strategy_id || "manual"}`, [{ label: s.source || "api", tone: "purple" }])).join("") : compactRow("No signals yet", "Submitted broker signals will appear here.");
    }
    const inboxCount = $("#signalInboxCount"); if (inboxCount) inboxCount.textContent = String(signals.length);
    const rt = $("#runtimeTable");
    if (rt) {
      const rows = [
        ["Control", halted ? "halted" : "armed", data.control?.reason || "none"],
        ["Approvals", data.execution?.require_approval ? "required" : "not required", data.execution?.submit_intent || "broker_order"],
        ["Runtime config", objSize(data.runtime), JSON.stringify(data.runtime || {}).slice(0, 80) || "default"],
        ["Protection state", objSize(data.protections), safeArray(data.protections?.rules).length ? "rules active" : "no active rules"],
      ];
      rt.innerHTML = rows.map(r => `<tr><td>${escapeHtml(r[0])}</td><td>${escapeHtml(r[1])}</td><td><small>${escapeHtml(r[2])}</small></td></tr>`).join("");
    }
    const auditBox = $("#dashboardAudit");
    if (auditBox) {
      auditBox.innerHTML = audit.slice(-6).reverse().map(event => compactRow(event.event_type || event.type || "audit", `${isoOrNow(event.created_at || event.timestamp)} · ${JSON.stringify(event.details || event.payload || {}).slice(0, 120)}`)).join("") || compactRow("No audit events", "Audit rows will appear after actions.");
    }
    const auditCount = $("#dashboardAuditCount"); if (auditCount) auditCount.textContent = String(audit.length);
  }

  function sampleSignalText() {
    const last = latestChartPriceFor(currentSymbol()) || live-dataReferencePrice(currentSymbol());
    const side = state.bracket?.side === "short" ? "SHORT" : "BUY";
    const entry = state.bracket?.entry || last;
    const sl = state.bracket?.stop || (side === "BUY" ? entry * 0.985 : entry * 1.015);
    const tp1 = state.bracket?.tp1 || (side === "BUY" ? entry * 1.025 : entry * 0.975);
    const tp2 = state.bracket?.tp2 || (side === "BUY" ? entry * 1.045 : entry * 0.955);
    return `${side} ${rawSymbol(currentSymbol())} $100 @ ${round(entry, 2)} SL @ ${round(sl, 2)} TP1 @ ${round(tp1, 2)} 50% TP2 @ ${round(tp2, 2)} 50% TRAIL 2% ACT 1% BE 1%`;
  }

  async function parseSignalTextFromUi() {
    const input = $("#signalTextInput");
    try {
      const payload = await api("/signals/parse-text", { method: "POST", body: { message: input?.value || sampleSignalText(), channel: $("#signalChannelInput")?.value || "operator" } });
      state.backend.parsedSignal = payload.signal;
      setJson("signalPayloadPreview", payload);
      const s = $("#signalPreviewState"); if (s) s.textContent = "parsed";
      setStatus("Signal parsed with Sentinel text parser.", "ok");
      renderSignalsPanel();
    } catch (err) { setStatus(`Signal parse failed: ${err.message || err}`, "error"); toast(err.message || String(err)); }
  }

  async function previewSignalTextFromUi() {
    const input = $("#signalTextInput");
    try {
      const payload = await api("/signals/preview-text", { method: "POST", body: { message: input?.value || sampleSignalText() } });
      state.backend.signalPreview = payload;
      setJson("signalPayloadPreview", payload);
      const s = $("#signalPreviewState"); if (s) s.textContent = payload.accepted === false ? "rejected" : "previewed";
      setStatus("Signal risk preview returned from Sentinel engine.", payload.accepted === false ? "warn" : "ok");
      renderSignalsPanel();
    } catch (err) { setStatus(`Signal preview failed: ${err.message || err}`, "error"); toast(err.message || String(err)); }
  }

  async function submitSignalTextFromUi() {
    const input = $("#signalTextInput");
    try {
      const payload = await api("/signals/submit-text", { method: "POST", body: { message: input?.value || sampleSignalText() } });
      setJson("signalPayloadPreview", payload);
      setStatus("Signal submitted to Sentinel broker/approval flow.", "ok");
      await refreshBackendState(false);
    } catch (err) { setStatus(`Submit failed: ${err.message || err}`, "error"); toast(err.message || String(err)); }
  }

  function renderSignalsPanel() {
    const signals = activeSignals();
    const approvals = activeApprovals();
    const pending = $("#pendingApprovalsList");
    if (pending) {
      pending.innerHTML = approvals.length ? approvals.map(a => {
        const sig = a.signal || a;
        return `<div class="compact-row"><div><b>${escapeHtml(sig.symbol || a.symbol || "pending signal")}</b><p>${escapeHtml(compactId(sig.signal_id || a.signal_id))} · ${escapeHtml(sig.side || "")} · ${escapeHtml(sig.strategy_id || "manual")}</p></div><div class="row-actions"><button data-approval-approve="${escapeHtml(sig.signal_id || a.signal_id)}">Approve</button><button data-approval-reject="${escapeHtml(sig.signal_id || a.signal_id)}">Reject</button></div></div>`;
      }).join("") : compactRow("No pending approvals", "Approval queue is empty.");
    }
    const count = $("#pendingApprovalCount"); if (count) count.textContent = String(approvals.length);
    const search = String($("#signalSearchInput")?.value || "").toLowerCase();
    const filtered = signals.filter(s => !search || JSON.stringify(s).toLowerCase().includes(search));
    const table = $("#signalHistoryTable");
    if (table) {
      table.innerHTML = filtered.slice(-80).reverse().map(s => `<tr><td>${escapeHtml(compactId(s.signal_id))}</td><td>${escapeHtml(s.symbol || "—")}</td><td>${escapeHtml(s.side || "—")}</td><td>${escapeHtml(s.quote_amount || s.base_amount || s.risk_pct || "—")}</td><td>${escapeHtml(s.strategy_id || "manual")}</td><td><button class="mini-tab" data-load-signal-ticket="${escapeHtml(s.signal_id)}">Load Ticket</button></td></tr>`).join("") || `<tr><td colspan="6"><small>No signals match.</small></td></tr>`;
    }
    const histCount = $("#signalHistoryCount"); if (histCount) histCount.textContent = String(filtered.length);
    if (!state.backend.parsedSignal && !state.backend.signalPreview) setJson("signalPayloadPreview", {});
  }

  async function approveSignal(signalId) {
    try {
      const result = await api(`/approvals/${encodeURIComponent(signalId)}/approve`, { method: "POST", body: {} });
      setJson("signalPayloadPreview", result);
      setStatus(`Approved ${signalId}.`, "ok");
      await refreshBackendState(false);
    } catch (err) { setStatus(`Approve failed: ${err.message || err}`, "error"); }
  }

  async function rejectSignal(signalId) {
    try {
      const result = await api(`/approvals/${encodeURIComponent(signalId)}/reject`, { method: "POST", body: { reason: $("#rejectReasonInput")?.value || "operator rejected" } });
      setJson("signalPayloadPreview", result);
      setStatus(`Rejected ${signalId}.`, "ok");
      await refreshBackendState(false);
    } catch (err) { setStatus(`Reject failed: ${err.message || err}`, "error"); }
  }

  function signalFromGuardianPlan() {
    const p = state.plan;
    if (!p) return null;
    return {
      symbol: rawSymbol(p.symbol),
      side: p.side === "short" ? "sell" : "buy",
      exchange: "broker",
      market_type: "swap",
      price: round(p.entry, 8),
      quote_amount: round(Math.min(Math.max(p.initialMargin || 0, 25), p.notional || 100), 2) || 100,
      risk_pct: round(p.riskPct || 1, 4),
      leverage: round(p.leverage || 1, 2),
      stop_loss_price: round(p.stopLoss, 8),
      take_profit_targets: [
        { trigger_price: round(p.takeProfit[0], 8), close_pct: "50" },
        { trigger_price: round(p.takeProfit[1], 8), close_pct: "50" },
      ],
      strategy_id: `guardian_${p.orderStyle || "manual"}`,
      max_slippage_bps: 100,
    };
  }

  function buildTicketPayload() {
    const mode = $("#ticketSizeModeInput")?.value || "quote";
    const size = $("#ticketSizeInput")?.value || "100";
    const payload = {
      symbol: rawSymbol($("#ticketSymbolInput")?.value || currentSymbol()),
      side: $("#ticketSideInput")?.value || "buy",
      exchange: "broker",
      market_type: "swap",
      price: $("#ticketPriceInput")?.value || undefined,
      stop_loss_price: $("#ticketStopInput")?.value || undefined,
      leverage: $("#ticketLeverageInput")?.value || "1",
      strategy_id: $("#ticketStrategyInput")?.value || "guardian_manual",
      max_slippage_bps: 100,
    };
    if (mode === "base") payload.base_amount = size;
    else if (mode === "risk") payload.risk_pct = size;
    else payload.quote_amount = size;
    const tp = $("#ticketTakeProfitInput")?.value;
    if (tp) payload.take_profit_targets = [{ trigger_price: tp, close_pct: "100" }];
    const trail = $("#ticketTrailingInput")?.value;
    if (trail) payload.trailing_stop_price = trail;
    const act = $("#ticketTrailActivationInput")?.value;
    if (act) payload.trailing_activation_price = act;
    const be = $("#ticketBreakevenInput")?.value;
    if (be) payload.breakeven_trigger_pct = be;
    Object.keys(payload).forEach(k => (payload[k] === undefined || payload[k] === "") && delete payload[k]);
    return payload;
  }

  function ticketAlertText(payload = buildTicketPayload()) {
    const size = payload.quote_amount ? `$${payload.quote_amount}` : payload.base_amount || `${payload.risk_pct}%`;
    const side = payload.side === "sell" ? "SHORT" : "BUY";
    const tp = payload.take_profit_targets?.[0]?.trigger_price ? ` TP @ ${payload.take_profit_targets[0].trigger_price}` : "";
    const sl = payload.stop_loss_price ? ` SL @ ${payload.stop_loss_price}` : "";
    const chartPrice = latestChartPriceFor(payload.symbol);
    return `${side} ${rawSymbol(payload.symbol)} ${size} @ ${payload.price || (Number.isFinite(chartPrice) ? chartPrice : "")}${sl}${tp}`.trim();
  }

  function populateTicketFromPayload(payload) {
    if (!payload) return;
    if ($("#ticketSymbolInput")) $("#ticketSymbolInput").value = rawSymbol(payload.symbol || currentSymbol());
    if ($("#ticketSideInput")) $("#ticketSideInput").value = payload.side === "sell" ? "sell" : "buy";
    if ($("#ticketSizeModeInput")) $("#ticketSizeModeInput").value = payload.base_amount ? "base" : payload.risk_pct && !payload.quote_amount ? "risk" : "quote";
    if ($("#ticketSizeInput")) $("#ticketSizeInput").value = payload.quote_amount || payload.base_amount || payload.risk_pct || "100";
    if ($("#ticketLeverageInput")) $("#ticketLeverageInput").value = payload.leverage || "1";
    if ($("#ticketPriceInput")) $("#ticketPriceInput").value = payload.price || "";
    if ($("#ticketStopInput")) $("#ticketStopInput").value = payload.stop_loss_price || "";
    if ($("#ticketTakeProfitInput")) $("#ticketTakeProfitInput").value = payload.take_profit_targets?.[0]?.trigger_price || payload.take_profit_price || "";
    if ($("#ticketTrailingInput")) $("#ticketTrailingInput").value = payload.trailing_stop_price || payload.trailing_stop_amount || "";
    if ($("#ticketTrailActivationInput")) $("#ticketTrailActivationInput").value = payload.trailing_activation_price || "";
    if ($("#ticketBreakevenInput")) $("#ticketBreakevenInput").value = payload.breakeven_trigger_pct || "";
    state.backend.ticketPayload = payload;
    renderDeskPanel();
  }

  async function previewTicketPayload() {
    const payload = buildTicketPayload();
    try {
      state.backend.ticketPayload = payload;
      const preview = await api("/signals/preview", { method: "POST", body: payload });
      state.backend.ticketPreview = preview;
      setJson("ticketJsonPreview", { payload, preview });
      setStatus("Trading ticket risk preview returned from Sentinel engine.", preview.accepted === false ? "warn" : "ok");
      renderDeskPanel();
    } catch (err) { setJson("ticketJsonPreview", { payload, error: err.message || String(err) }); setStatus(`Ticket preview failed: ${err.message || err}`, "error"); }
  }

  async function submitTicketPayload() {
    const payload = buildTicketPayload();
    try {
      const result = await api("/signals/submit", { method: "POST", body: payload });
      state.backend.ticketPayload = payload;
      state.backend.ticketPreview = result;
      setJson("ticketJsonPreview", { payload, result });
      setStatus("Ticket submitted to Sentinel broker/approval flow.", "ok");
      await refreshBackendState(false);
    } catch (err) { setJson("ticketJsonPreview", { payload, error: err.message || String(err) }); setStatus(`Ticket submit failed: ${err.message || err}`, "error"); }
  }

  function renderDeskPanel() {
    const strategySelect = $("#ticketStrategyInput");
    if (strategySelect) {
      const current = strategySelect.value;
      const strategies = state.backend.strategies.length ? state.backend.strategies : [{ name: "manual", signal_defaults: {} }];
      strategySelect.innerHTML = strategies.map(p => `<option value="${escapeHtml(p.name || p.strategy_id || "manual")}">${escapeHtml(strategyTitle(p.name || p.strategy_id || "manual"))}</option>`).join("");
      if (current) strategySelect.value = current;
    }
    const payload = state.backend.ticketPayload || buildTicketPayload();
    const preview = state.backend.ticketPreview;
    const list = $("#ticketPreflightList");
    if (list) {
      list.innerHTML = [
        compactRow("Payload geometry", `${payload.side || "—"} ${payload.symbol || "—"} @ ${payload.price || "market"} · SL ${payload.stop_loss_price || "—"} · TP ${payload.take_profit_targets?.[0]?.trigger_price || "—"}`),
        compactRow("Runtime decision", preview ? JSON.stringify({ accepted: preview.accepted, approval_required: preview.approval_required, reason_codes: preview.reason_codes || preview.runtime_controls?.reason_codes }).slice(0, 180) : "Preview not run yet."),
        compactRow("Live trading", state.backend.liveStatus?.bitunix?.live_execution_enabled ? "Bitunix live route is enabled but still requires preview ID + manual confirmation." : "Locked until env, approval, secret, credentials, risk, and preview gates are satisfied.", [{ label: state.backend.liveStatus?.bitunix?.live_execution_enabled ? "armed" : "locked", tone: "warn" }]),
      ].join("");
    }
    if (!state.backend.ticketPreview) setJson("ticketJsonPreview", payload);
    renderDeskTable();
  }

  function renderDeskTable() {
    const kind = state.backend.deskTable || "positions";
    const head = $("#deskTableHead");
    const body = $("#deskTableBody");
    if (!head || !body) return;
    const search = String($("#deskSearchInput")?.value || "").toLowerCase();
    if (kind === "orders") {
      head.innerHTML = `<tr><th>ID</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Price</th><th>Kind</th><th>Action</th></tr>`;
      const rows = activeOrders().filter(o => !search || JSON.stringify(o).toLowerCase().includes(search)).slice(-100).reverse();
      body.innerHTML = rows.map(o => `<tr><td>${escapeHtml(compactId(o.signal_id || o.order_id || o.id))}</td><td>${escapeHtml(o.symbol || "—")}</td><td>${escapeHtml(o.side || "—")}</td><td>${escapeHtml(o.quantity || o.base_amount || "—")}</td><td>${escapeHtml(o.price || "—")}</td><td>${escapeHtml(o.exit_kind || o.kind || "entry")}</td><td><button class="mini-tab" data-inspect-order="${escapeHtml(o.signal_id || o.order_id || o.id || "")}">Inspect</button></td></tr>`).join("") || `<tr><td colspan="7"><small>No orders.</small></td></tr>`;
    } else {
      head.innerHTML = `<tr><th>Symbol</th><th>Qty</th><th>Avg Price</th><th>Notional</th><th>Action</th></tr>`;
      const rows = activePositions().filter(o => !search || JSON.stringify(o).toLowerCase().includes(search));
      body.innerHTML = rows.map(o => `<tr><td>${escapeHtml(o.symbol || "—")}</td><td>${escapeHtml(o.quantity || o.base_amount || "—")}</td><td>${escapeHtml(o.average_price || o.avg_price || "—")}</td><td>${escapeHtml(o.notional || "—")}</td><td><button class="mini-tab" data-inspect-position="${escapeHtml(o.symbol || "")}">Inspect</button></td></tr>`).join("") || `<tr><td colspan="5"><small>No open positions.</small></td></tr>`;
    }
  }

  async function selectDeskSymbol(symbol) {
    const normalized = setCurrentSymbol(symbol);
    resetDeskSymbolFields();
    const wasStreaming = Boolean(state.backend.candleConnected || state.backend.candleStream);
    loadLive Data($("#scenarioInput")?.value || "volatile");
    if (wasStreaming) {
      state.backend.candleEventCount = 0;
      startCandleStream();
    }
    if (state.backend.data) await loadServerDrawings(false, true);
    syncMarkPriceFromChart();
    renderDeskPanel();
    setStatus(`Trading Desk switched to ${normalized}.`, "ok");
  }

  async function previewOrApplyMark(apply = false) {
    const symbol = rawSymbol($("#markSymbolInput")?.value || currentSymbol());
    const chartPrice = latestChartPriceFor(symbol);
    const price = $("#markPriceInput")?.value || (Number.isFinite(chartPrice) ? chartPrice : "");
    if (!price) {
      setStatus(`Enter a mark price or load candles for ${symbol} before marking the broker engine.`, "warn");
      return;
    }
    const path = apply ? "/market/price" : "/market/price/preview";
    try {
      const result = await api(path, { method: "POST", body: { symbol, price, include_order_metadata: true } });
      const box = $("#markResultBox"); if (box) box.innerHTML = compactRow(apply ? "Mark applied" : "Mark preview", JSON.stringify(result).slice(0, 300));
      setStatus(apply ? "Market mark applied to broker engine." : "Market mark preview calculated.", "ok");
      if (apply) await refreshBackendState(false);
    } catch (err) { setStatus(`Mark update failed: ${err.message || err}`, "error"); }
  }

  function renderRiskPanel() {
    const data = activeData();
    const account = data.account || {};
    const risk = data.risk || {};
    const kpis = $("#riskKpis");
    if (kpis) {
      const summary = state.backend.bracketRisk?.totals || state.backend.bracketRisk || {};
      kpis.innerHTML = [
        opsKpi("Max Order", money(safeNumber(risk.max_order_notional)), "risk config", "purple"),
        opsKpi("Daily P&L", money(safeNumber(account.daily_pnl)), "broker account", safeNumber(account.daily_pnl) < 0 ? "bad" : "good"),
        opsKpi("Worst Case Loss", money(safeNumber(summary.worst_case_loss)), `${state.backend.brackets.length} brackets`, safeNumber(summary.worst_case_loss) ? "warn" : "good"),
        opsKpi("Guardian Score", String(state.plan?.score ?? "—"), "local TP/SL plan", (state.plan?.score || 0) >= 80 ? "good" : "warn"),
      ].join("");
    }
    const guardList = $("#riskGuardList");
    if (guardList) {
      const guards = state.plan?.guards || [];
      guardList.innerHTML = guards.length ? guards.map(it => `<div class="guard-item ${it.status}"><div class="guard-icon">${it.status === "pass" ? "✓" : it.status === "fail" ? "×" : "!"}</div><div><b>${escapeHtml(it.title)}</b><p>${escapeHtml(it.detail)}</p></div></div>`).join("") : compactRow("No Guardian bracket", "Draw a bracket on the chart to populate risk guardrails.");
    }
    const riskSummary = $("#riskGuardSummary"); if (riskSummary) riskSummary.textContent = state.plan?.guards ? `${state.plan.guards.length} checks` : "local";
    renderBracketLedger();
  }

  async function previewFuturesRisk() {
    const payload = signalFromGuardianPlan() || buildTicketPayload();
    const notional = state.plan?.notional || safeNumber(payload.quote_amount, 100);
    try {
      const result = await api("/futures/risk/preview", { method: "POST", body: {
        symbol: payload.symbol,
        side: payload.side,
        entry_price: payload.price || latestChartPriceFor(payload.symbol),
        stop_loss_price: payload.stop_loss_price,
        notional,
        leverage: payload.leverage || 1,
        maintenance_margin_pct: $("#futuresMaintenanceInput")?.value || "0.5",
        funding_rate_bps: $("#futuresFundingInput")?.value || "0",
      } });
      setJson("futuresRiskPreview", result);
      const s = $("#futuresRiskState"); if (s) s.textContent = result.accepted === false ? "blocked" : "ok";
      setStatus("Futures risk preview returned from backend.", result.accepted === false ? "warn" : "ok");
    } catch (err) { setJson("futuresRiskPreview", { error: err.message || String(err) }); setStatus(`Futures risk failed: ${err.message || err}`, "error"); }
  }

  function renderBracketLedger() {
    const table = $("#bracketLedgerTable"); if (!table) return;
    const brackets = state.backend.brackets || [];
    table.innerHTML = brackets.map(b => {
      const s = b.summary || {};
      return `<tr><td>${escapeHtml(compactId(b.signal_id))}</td><td>${escapeHtml(b.symbol || "—")}</td><td>${escapeHtml(b.direction || "—")}</td><td>${escapeHtml(s.worst_case_loss || "—")}</td><td>${escapeHtml(s.total_target_reward_risk_ratio || s.first_target_reward_risk_ratio || "—")}</td><td><button class="mini-tab" data-bracket-action="amend-stop" data-signal-id="${escapeHtml(b.signal_id)}">Stop</button><button class="mini-tab" data-bracket-action="amend-trailing" data-signal-id="${escapeHtml(b.signal_id)}">Trail</button><button class="mini-tab" data-bracket-action="amend-tp" data-signal-id="${escapeHtml(b.signal_id)}">TP</button><button class="mini-tab" data-bracket-action="breakeven" data-signal-id="${escapeHtml(b.signal_id)}">BE</button><button class="mini-tab" data-bracket-action="lock" data-signal-id="${escapeHtml(b.signal_id)}">Lock</button><button class="mini-tab" data-bracket-action="close-protective" data-signal-id="${escapeHtml(b.signal_id)}">Protect</button><button class="mini-tab" data-bracket-action="cancel" data-signal-id="${escapeHtml(b.signal_id)}">Cancel</button><button class="mini-tab" data-bracket-action="close" data-signal-id="${escapeHtml(b.signal_id)}">Close</button></td></tr>`;
    }).join("") || `<tr><td colspan="6"><small>No active brackets.</small></td></tr>`;
    const count = $("#bracketLedgerCount"); if (count) count.textContent = String(brackets.length);
  }

  async function bracketAction(signalId, action) {
    const map = { breakeven: "breakeven", cancel: "cancel", close: "close", lock: "lock-profit", "amend-stop": "stop", "amend-trailing": "trailing-stop", "amend-tp": "take-profit", "close-protective": "close-protective" };
    const path = `/brackets/${encodeURIComponent(signalId)}/${map[action] || action}`;
    const body = action === "lock" ? { lock_profit_pct: "0.25", reason: "guardian lock" } : { reason: `guardian ${action}` };
    if (action === "amend-stop" || action === "amend-trailing" || action === "amend-tp") {
      const label = action === "amend-stop" ? "protective stop" : action === "amend-trailing" ? "trailing stop" : "take-profit";
      const fallback = action === "amend-stop" ? state.plan?.stopLoss : action === "amend-tp" ? state.plan?.takeProfit?.[0] : state.candles.at(-1)?.close;
      const trigger = window.prompt(`New ${label} trigger price`, Number.isFinite(fallback) ? String(round(fallback, 8)) : "");
      if (!trigger) return;
      body.trigger_price = trigger;
    }
    try {
      const result = await api(path, { method: "POST", body });
      setJson("futuresRiskPreview", result);
      setStatus(`Bracket ${action} completed for ${signalId}.`, "ok");
      await refreshBackendState(false);
    } catch (err) { setStatus(`Bracket ${action} failed: ${err.message || err}`, "error"); }
  }

  function renderVcpPanel() {
    const v = state.vcp;
    const kpis = $("#vcpKpis");
    if (kpis) {
      kpis.innerHTML = [
        opsKpi("VCP Score", String(Math.round(v?.score || 0)), v?.status || "scanning", (v?.score || 0) >= 60 ? "good" : "warn"),
        opsKpi("Pivot", priceFmt(v?.pivot), "breakout gate", "purple"),
        opsKpi("Final Low", priceFmt(v?.finalLow), "stop anchor", "warn"),
        opsKpi("Volume Dry-Up", String(v?.volDry || 0), `${safeArray(v?.contractions).length} contractions`, "good"),
      ].join("");
    }
    const list = $("#vcpContractionList");
    if (list) {
      const contractions = safeArray(v?.contractions);
      list.innerHTML = contractions.length ? contractions.map((c, i) => compactRow(`Contraction ${i + 1}`, `Pullback ${pct(c.pct)} · bars ${c.startIndex} to ${c.endIndex} · avg vol ${priceFmt(c.volume)}`)).join("") : compactRow("No clean contraction map", "Load VCP live-data or analyze a tighter price series.");
    }
    const count = $("#vcpContractionCount"); if (count) count.textContent = String(safeArray(v?.contractions).length);
    const notes = $("#vcpSafetyNotes");
    if (notes) notes.innerHTML = [
      compactRow("Entry gate", "Prefer pivot confirmation or a controlled retest; avoid chasing extended candles."),
      compactRow("Stop anchor", "Place stop beyond final contraction low/high plus volatility buffer, not in the middle of noise."),
      compactRow("Volume", "A valid contraction should show dry-up before expansion; sudden heavy selling into pivot weakens the setup."),
    ].join("");
  }

  async function quickAnalyzeFromPlan(targetId = "vcpAnalyzePreview") {
    const signal = signalFromGuardianPlan() || buildTicketPayload();
    const prices = state.candles.slice(-80).map(c => c.close);
    try {
      const result = await api("/analysis/signal", { method: "POST", body: { signal, prices, close_final_positions: true } });
      setJson(targetId, result);
      const s = $("#vcpAnalyzeState"); if (s) s.textContent = result.accepted === false ? "blocked" : "complete";
      setStatus("Quick analysis returned from Sentinel backend.", "ok");
    } catch (err) { setJson(targetId, { signal, error: err.message || String(err) }); setStatus(`Analyze failed: ${err.message || err}`, "error"); }
  }

  function renderDrawingsPanel() {
    const dl = $("#drawingList");
    if (dl) dl.innerHTML = state.drawings.length ? state.drawings.map((d, i) => compactRow(`${i + 1}. ${titleCase(d.type)}`, JSON.stringify(d).slice(0, 180))).join("") : compactRow("No drawings", "Use trendline, horizontal, or zone tools from the chart or this panel.");
    const dc = $("#drawingCount"); if (dc) dc.textContent = String(state.drawings.length);
    const ds = $("#drawingServerState");
    if (ds) {
      const saved = state.backend.serverDrawings;
      ds.innerHTML = saved ? compactRow("Server storage", `${saved.count ?? safeArray(saved.drawings).length} saved for ${saved.symbol || drawingSymbol()} · ${saved.updated_at ? isoOrNow(saved.updated_at) : "not timestamped"}`, [{ label: "persistent", tone: "purple" }]) : compactRow("Server storage", "No server-saved lines loaded for this symbol yet.", [{ label: "local only", tone: "warn" }]);
    }
    const nl = $("#nearestLevelList");
    if (nl) {
      const last = state.candles.at(-1)?.close;
      const rows = state.supports.slice().sort((a, b) => Math.abs(a.price - last) - Math.abs(b.price - last)).slice(0, 8);
      nl.innerHTML = rows.length ? rows.map(l => compactRow(`${titleCase(l.kind)} ${priceFmt(l.price)}`, `Zone ${priceFmt(l.zoneLow)} - ${priceFmt(l.zoneHigh)} · touches ${l.touches || 0}`)).join("") : compactRow("No S/R levels", "Load candles to compute levels.");
    }
    const warLevels = $("#warRoomLevelsTable");
    if (warLevels) {
      const levels = safeArray(state.backend.warAnalysis?.overlays?.support_resistance);
      warLevels.innerHTML = levels.slice(0, 30).map(l => `<tr><td>${escapeHtml(l.kind || "—")}</td><td>${escapeHtml(priceFmt(l.price))}</td><td>${escapeHtml(priceFmt(l.zone_low))} - ${escapeHtml(priceFmt(l.zone_high))}</td><td>${escapeHtml(l.touches || "—")}</td><td>${escapeHtml(priceFmt(l.score))}</td></tr>`).join("") || `<tr><td colspan="5"><small>Run War Room Auto Map to load backend levels.</small></td></tr>`;
    }
    const wrs = $("#warRoomLevelState"); if (wrs) wrs.textContent = state.backend.warAnalysis ? "loaded" : "not loaded";
  }

  function renderPortfolioPanel() {
    const data = activeData();
    const account = data.account || {};
    const kpis = $("#portfolioKpis");
    if (kpis) kpis.innerHTML = [
      opsKpi("Equity", money(safeNumber(account.equity)), "broker account", "purple"),
      opsKpi("Daily P&L", money(safeNumber(account.daily_pnl)), `${account.consecutive_losses || 0} losses`, safeNumber(account.daily_pnl) < 0 ? "bad" : "good"),
      opsKpi("Open Risk", money(safeNumber(account.open_risk_amount)), "aggregate stops", safeNumber(account.open_risk_amount) ? "warn" : "good"),
      opsKpi("Bracket Coverage", String(state.backend.coverage?.bracket_count ?? state.backend.brackets.length), "active exits", "warn"),
    ].join("");
    const limits = $("#exposureLimits");
    if (limits) {
      const risk = data.risk || {};
      limits.innerHTML = [
        compactRow("Order cap", `Max order notional ${money(safeNumber(risk.max_order_notional))}`),
        compactRow("Daily stop", `Max daily loss ${money(safeNumber(risk.max_daily_loss))}`),
        compactRow("Symbol concentration", `Max symbol notional ${money(safeNumber(risk.max_symbol_open_notional))}`),
        compactRow("Approval mode", data.execution?.require_approval ? "Approval queue is required." : "Broker orders may submit directly."),
      ].join("");
    }
    const table = $("#portfolioPositionsTable");
    if (table) table.innerHTML = activePositions().map(p => `<tr><td>${escapeHtml(p.symbol || "—")}</td><td>${escapeHtml(p.quantity || "—")}</td><td>${escapeHtml(p.average_price || p.avg_price || "—")}</td><td>${escapeHtml(p.notional || "—")}</td><td>${escapeHtml(p.unrealized_pnl || "—")}</td></tr>`).join("") || `<tr><td colspan="5"><small>No open positions.</small></td></tr>`;
    const pc = $("#portfolioPositionCount"); if (pc) pc.textContent = String(activePositions().length);
  }

  function strategyCategory(preset) {
    const raw = `${preset.name || ""} ${preset.description || ""} ${JSON.stringify(preset.signal_defaults || {})}`.toLowerCase();
    if (raw.includes("grid")) return "grid";
    if (raw.includes("dca")) return "dca";
    return "signal";
  }

  function renderStrategiesPanel() {
    const cards = $("#strategyCards"); if (!cards) return;
    const filter = $("#strategyFilterInput")?.value || "all";
    const search = String($("#strategySearchInput")?.value || "").toLowerCase();
    const sort = $("#strategySortInput")?.value || "name";
    const pins = new Set(state.backend.strategyPins || []);
    let presets = [...(state.backend.strategies || [])];
    if (!presets.length) presets = [{ name: "guardian_manual", description: "Manual Guardian bracket ticket", signal_defaults: { side: "buy", market_type: "swap" } }];
    presets = presets.filter(p => (filter === "all" || strategyCategory(p) === filter) && (!search || JSON.stringify(p).toLowerCase().includes(search)));
    presets.sort((a, b) => {
      if (sort === "pinned") return Number(pins.has(b.name)) - Number(pins.has(a.name)) || String(a.name).localeCompare(String(b.name));
      if (sort === "type") return strategyCategory(a).localeCompare(strategyCategory(b)) || String(a.name).localeCompare(String(b.name));
      return String(a.name).localeCompare(String(b.name));
    });
    cards.innerHTML = presets.map(p => `<article class="strategy-card ${pins.has(p.name) ? "pinned" : ""}"><h3>${escapeHtml(strategyTitle(p.name))}</h3><p>${escapeHtml(p.description || safeArray(p.entry_logic).join(" · ") || "Preset from Sentinel backend.")}</p><div class="meta"><span class="chip purple">${escapeHtml(strategyCategory(p))}</span><span class="chip">${escapeHtml(p.suggested_bracket_template || "manual bracket")}</span></div><div class="row-actions"><button data-pin-strategy="${escapeHtml(p.name)}">${pins.has(p.name) ? "Unpin" : "Pin"}</button><button data-load-strategy-ticket="${escapeHtml(p.name)}">Load Ticket</button><button data-analysis-strategy="${escapeHtml(p.name)}">Analyze</button><button data-preview-strategy="${escapeHtml(p.name)}">Checklist</button></div></article>`).join("") || `<div class="compact-row"><b>No strategies</b><p>No presets match the current filter.</p></div>`;
  }

  function strategyByName(name) { return (state.backend.strategies || []).find(p => p.name === name); }

  function previewStrategy(name) {
    const preset = strategyByName(name);
    setJson("strategyPreviewJson", preset || { error: "strategy not found", name });
    const s = $("#strategyPreviewState"); if (s) s.textContent = name;
  }

  function loadStrategyTicket(name) {
    const preset = strategyByName(name) || {};
    const d = preset.signal_defaults || {};
    const symbol = rawSymbol(d.symbol || currentSymbol());
    const chartPrice = latestChartPriceFor(symbol);
    populateTicketFromPayload({
      symbol,
      side: d.side || "buy",
      market_type: d.market_type || "swap",
      exchange: d.exchange || "broker",
      quote_amount: d.quote_amount || "100",
      leverage: d.leverage || "3",
      strategy_id: d.strategy_id || preset.name || name,
      price: Number.isFinite(chartPrice) ? round(chartPrice, 2) : "",
    });
    switchView("desk");
  }

  async function analysisStrategy(name) {
    const preset = strategyByName(name) || {};
    const payload = { ...buildTicketPayload(), strategy_id: preset.name || name };
    if (!payload.stop_loss_price && state.plan?.stopLoss) payload.stop_loss_price = round(state.plan.stopLoss, 8);
    if (!payload.take_profit_targets && state.plan?.takeProfit) payload.take_profit_targets = [{ trigger_price: round(state.plan.takeProfit[0], 8), close_pct: "100" }];
    const chartPrice = latestChartPriceFor(payload.symbol);
    if (!payload.price && Number.isFinite(chartPrice)) payload.price = round(chartPrice, 8);
    try {
      const result = await api("/analysis/signal", { method: "POST", body: { signal: payload, prices: state.candles.slice(-60).map(c => c.close), close_final_positions: true } });
      setJson("strategyPreviewJson", { strategy: preset, analysis: result });
      const s = $("#strategyPreviewState"); if (s) s.textContent = `${name} analysised`;
    } catch (err) { setJson("strategyPreviewJson", { strategy: preset, error: err.message || String(err), signal: payload }); }
  }

  function renderExchangesPanel() {
    const exSearch = String($("#exchangeSearchInput")?.value || "").toLowerCase();
    renderLiveExecutionPanel();
    const platforms = state.backend.platforms || [];
    const pt = $("#platformTable");
    if (pt) pt.innerHTML = platforms.map(p => `<tr><td>${escapeHtml(p.name || p.id || p.exchange_id || "—")}</td><td>${escapeHtml(p.status || p.state || "available")}</td><td>${escapeHtml(p.broker_trading ? "yes" : p.broker_supported ? "yes" : "—")}</td><td>${escapeHtml(p.live_trading ? "enabled" : "locked")}</td></tr>`).join("") || `<tr><td colspan="4"><small>No platforms loaded.</small></td></tr>`;
    const pc = $("#platformCount"); if (pc) pc.textContent = String(platforms.length);
    const list = $("#exchangeList");
    const exchanges = (state.backend.exchanges || []).filter(e => !exSearch || JSON.stringify(e).toLowerCase().includes(exSearch));
    if (list) list.innerHTML = exchanges.slice(0, 120).map(e => {
      const id = e.id || e.exchange_id || e.name || e;
      return `<div class="compact-row"><div><b>${escapeHtml(id)}</b><p>${escapeHtml(e.name || e.status || "exchange adapter")}</p></div><div class="row-actions"><button data-venue-status="${escapeHtml(id)}">Status</button><button data-venue-capabilities="${escapeHtml(id)}">Capabilities</button><button data-venue-integration="${escapeHtml(id)}">Integration</button></div></div>`;
    }).join("") || compactRow("No venues", "No exchange rows match the filter.");
    const ec = $("#exchangeCount"); if (ec) ec.textContent = String(exchanges.length);
  }

  async function loadVenueJson(exchangeId, kind) {
    const path = kind === "status"
      ? `/exchanges/${encodeURIComponent(exchangeId)}/ccxt/status`
      : kind === "integration"
        ? `/exchanges/${encodeURIComponent(exchangeId)}/integration`
        : `/exchanges/${encodeURIComponent(exchangeId)}/capabilities`;
    try {
      const payload = await api(path);
      state.backend.selectedVenueJson = payload;
      setJson("venueJsonPreview", payload);
      setStatus(`${strategyTitle(exchangeId)} ${kind} loaded.`, "ok");
    } catch (err) { setJson("venueJsonPreview", { exchangeId, kind, error: err.message || String(err) }); setStatus(`Venue ${kind} failed: ${err.message || err}`, "error"); }
  }

  async function loadBitunixTickers() {
    try {
      const symbols = $("#bitunixSymbolsInput")?.value || "BTCUSDT,ETHUSDT,SOLUSDT";
      const payload = await api(`/exchanges/bitunix/futures/tickers?symbols=${encodeURIComponent(symbols)}`);
      state.backend.selectedVenueJson = payload;
      setJson("venueJsonPreview", payload);
      setStatus("Bitunix futures tickers loaded.", "ok");
    } catch (err) { setJson("venueJsonPreview", { error: err.message || String(err) }); setStatus(`Bitunix ticker load failed: ${err.message || err}`, "error"); }
  }

  async function checkBitunixAccount() {
    try {
      const payload = await api("/exchanges/bitunix/futures/account?margin_coin=USDT");
      setJson("venueJsonPreview", payload);
      setStatus("Bitunix account check returned.", "ok");
    } catch (err) { setJson("venueJsonPreview", { error: err.message || String(err) }); setStatus(`Bitunix account check failed: ${err.message || err}`, "error"); }
  }

  function renderWarRoomPanel() {
    const features = state.backend.warFeatures;
    const list = $("#warFeatureList");
    if (list) {
      const flags = features?.feature_flags || {};
      list.innerHTML = Object.entries(flags).map(([k, v]) => compactRow(strategyTitle(k), v ? "enabled" : "disabled", [{ label: v ? "on" : "off", tone: v ? "good" : "warn" }])).join("") || compactRow("Features not loaded", "Refresh backend state to read /war-room/features.");
    }
    const fs = $("#warFeatureState"); if (fs) fs.textContent = features ? "loaded" : "loading";
    const why = $("#warRoomWhy");
    const analysis = state.backend.warAnalysis;
    if (why) {
      const w = analysis?.signals?.why || {};
      why.innerHTML = analysis ? [
        compactRow("How", w.headline || analysis.signals?.recommendation || "Auto-map generated a market structure summary."),
        compactRow("When", `Primary bias ${analysis.signals?.primary_bias || "—"}; wait for trigger and invalidation confirmation.`),
        compactRow("Why", safeArray(w.reasons).join(" · ") || JSON.stringify(analysis.signals || {}).slice(0, 180)),
      ].join("") : compactRow("No analysis yet", "Run Auto Map or Analyze Current Candles.");
    }
    const stateEl = $("#warRoomAnalysisState"); if (stateEl) stateEl.textContent = state.backend.warTicket ? "ticket" : analysis ? "analysis" : "empty";
  }

  function guardianCandlesForApi() {
    return state.candles.map(c => ({ time: c.time, open: c.open, high: c.high, low: c.low, close: c.close, volume: c.volume || 0 }));
  }

  async function warRoomLive Data() {
    try {
      const payload = await api(`/war-room/live-data?symbol=${encodeURIComponent(rawSymbol(currentSymbol()))}&timeframe=${encodeURIComponent(currentTimeframe())}&bars=${Math.max(80, state.candles.length || 180)}`);
      state.backend.warAnalysis = payload;
      if (payload.candles?.length) {
        state.candles = payload.candles.map(c => ({...c, open: +c.open, high: +c.high, low: +c.low, close: +c.close, volume: +c.volume || 0 }));
        markCandleSeries(currentSymbol(), currentTimeframe(), "war-room");
        updateAll();
        syncMarkPriceFromChart();
      }
      setJson("warRoomJsonPreview", payload);
      setStatus("War Room auto-map loaded.", "ok");
      renderBackendPanels();
    } catch (err) { setJson("warRoomJsonPreview", { error: err.message || String(err) }); setStatus(`War Room live-data failed: ${err.message || err}`, "error"); }
  }

  async function warRoomAnalyze() {
    try {
      const payload = await api("/war-room/analyze", { method: "POST", body: { symbol: rawSymbol(currentSymbol()), timeframe: currentTimeframe(), candles: guardianCandlesForApi(), settings: { posture: "balanced", risk: { account_equity: safeNumber($("#equityInput")?.value, 10000), risk_pct: safeNumber($("#riskPctInput")?.value, 1) } } } });
      state.backend.warAnalysis = payload;
      setJson("warRoomJsonPreview", payload);
      setStatus("War Room analysis completed.", "ok");
      renderBackendPanels();
    } catch (err) { setJson("warRoomJsonPreview", { error: err.message || String(err) }); setStatus(`War Room analyze failed: ${err.message || err}`, "error"); }
  }

  async function warRoomTicket() {
    try {
      if (!state.backend.warAnalysis) await warRoomAnalyze();
      const payload = await api("/war-room/ticket", { method: "POST", body: { symbol: rawSymbol(currentSymbol()), timeframe: currentTimeframe(), venue: "broker", market_type: "swap", side: state.bracket?.side || undefined, account_equity: safeNumber($("#equityInput")?.value, 10000), risk_pct: safeNumber($("#riskPctInput")?.value, 1), leverage: safeNumber($("#leverageInput")?.value, 1), candles: guardianCandlesForApi(), settings: { posture: "balanced" } } });
      state.backend.warTicket = payload;
      setJson("warRoomJsonPreview", payload);
      if (payload.signal) populateTicketFromPayload(payload.signal);
      setStatus("War Room ticket built and loaded into Trading Desk.", "ok");
      renderBackendPanels();
    } catch (err) { setJson("warRoomJsonPreview", { error: err.message || String(err) }); setStatus(`War Room ticket failed: ${err.message || err}`, "error"); }
  }

  async function warRoomAnalyze() {
    try {
      const payload = await api("/war-room/analysis", { method: "POST", body: { symbol: rawSymbol(currentSymbol()), timeframe: currentTimeframe(), candles: guardianCandlesForApi(), settings: { posture: "balanced" } } });
      setJson("warRoomJsonPreview", payload);
      setStatus("War Room quick analysis completed.", "ok");
    } catch (err) { setJson("warRoomJsonPreview", { error: err.message || String(err) }); setStatus(`War Room analysis failed: ${err.message || err}`, "error"); }
  }

  async function submitWarRoomSignal() {
    const signal = state.backend.warTicket?.signal;
    if (!signal) { await warRoomTicket(); }
    const payload = state.backend.warTicket?.signal;
    if (!payload) return;
    try {
      const result = await api("/signals/submit", { method: "POST", body: payload });
      setJson("warRoomJsonPreview", { signal: payload, result });
      setStatus("War Room signal submitted to broker/approval flow.", "ok");
      await refreshBackendState(false);
    } catch (err) { setJson("warRoomJsonPreview", { signal: payload, error: err.message || String(err) }); setStatus(`War Room submit failed: ${err.message || err}`, "error"); }
  }

  function renderAuditPanel() {
    const table = $("#auditTable"); if (!table) return;
    const search = String($("#auditSearchInput")?.value || "").toLowerCase();
    const filter = $("#auditFilterInput")?.value || "all";
    const rows = activeAudit().filter(e => {
      const text = JSON.stringify(e).toLowerCase();
      const type = String(e.event_type || e.type || "").toLowerCase();
      return (!search || text.includes(search)) && (filter === "all" || type.includes(filter));
    }).slice(-400).reverse();
    table.innerHTML = rows.map(e => `<tr><td>${escapeHtml(isoOrNow(e.created_at || e.timestamp))}</td><td>${escapeHtml(e.event_type || e.type || "audit")}</td><td><small>${escapeHtml(JSON.stringify(e.details || e.payload || {}).slice(0, 260))}</small></td><td><button class="mini-tab" data-audit-inspect='${escapeHtml(JSON.stringify(e))}'>Inspect</button></td></tr>`).join("") || `<tr><td colspan="4"><small>No audit events match.</small></td></tr>`;
  }

  function exportAuditCsv() {
    const rows = activeAudit();
    const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
    const csv = ["time,event_type,details", ...rows.map(e => [e.created_at || e.timestamp || "", e.event_type || e.type || "", JSON.stringify(e.details || e.payload || {})].map(esc).join(","))].join("\n");
    downloadText(`sentinel-guardian-audit-${Date.now()}.csv`, csv, "text/csv");
  }

  function renderDataPanel() {
    const count = $("#dataCandleCount"); if (count) count.textContent = String(state.candles.length);
    setJson("dataPreviewJson", state.candles.slice(-8));
    const list = $("#dataStatusList");
    if (list) list.innerHTML = [
      compactRow("Source", state.edge ? `Edge ${state.edge.mode} packet for ${state.edge.symbol}` : state.backend.candleConnected ? "Bitunix candle WebSocket / REST stream" : "Local/live-data candles"),
      compactRow("Bars", `${state.candles.length} candles · ${currentTimeframe()} · ${currentSymbol()}`),
      compactRow("ATR", priceFmt(state.atr), [{ label: "computed", tone: "purple" }]),
      compactRow("Backend", state.backend.data ? "Sentinel Chain API connected." : "No API state loaded yet."),
      compactRow("Edge stream", state.backend.edgeConnected ? `${state.backend.edgeEventCount} events received.` : "Disconnected.", [{ label: state.backend.edgeConnected ? "streaming" : "offline", tone: state.backend.edgeConnected ? "good" : "warn" }]),
      compactRow("Candle stream", state.backend.candleConnected ? `${state.backend.candleEventCount} updates received.` : "Disconnected.", [{ label: state.backend.candleConnected ? "streaming" : "idle", tone: state.backend.candleConnected ? "good" : "warn" }]),
      compactRow("Latest Edge", state.backend.edgeLatest?.count ? `${state.backend.edgeLatest.count} snapshot(s) cached on server.` : "No Edge snapshots cached yet."),
    ].join("");
  }

  async function loadPanelPastedData() {
    try {
      const raw = $("#panelDataInput")?.value || "";
      const candles = parsePastedData(raw);
      if (candles.length < 20) throw new Error("Need at least 20 valid candles.");
      state.edge = null; state.candles = candles; state.drawings = []; state.bracket = null;
      markCandleSeries(currentSymbol(), currentTimeframe(), "manual");
      updateAll(); switchView("chart"); toast(`Loaded ${candles.length} candles.`);
      syncMarkPriceFromChart();
    } catch (err) { setStatus(`Panel data load failed: ${err.message || err}`, "error"); toast(err.message || String(err)); }
  }

  async function loadBitunixCandles() {
    const symbol = rawSymbol(currentSymbol());
    const interval = currentTimeframe();
    const limit = clamp(Math.round(safeNumber($("#barsInput")?.value, 180)), 80, 420);
    try {
      const payload = await api(`/exchanges/bitunix/futures/klines?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}&limit=${limit}`);
      const candles = normalizeIncomingCandles(payload.candles);
      if (candles.length < 20) throw new Error("Bitunix returned too few valid candles.");
      state.edge = null; state.candles = candles; state.drawings = []; state.bracket = null;
      markCandleSeries(symbol, interval, "bitunix");
      updateAll();
      syncMarkPriceFromChart();
      await loadServerDrawings(false, true);
      setStatus(`Loaded ${candles.length} Bitunix candles.`, "ok"); switchView("chart");
    } catch (err) { setStatus(`Bitunix candle load failed: ${err.message || err}`, "error"); }
  }


  async function loadLiveStatus(showToast = false) {
    try {
      const payload = await api("/guardian/live/status");
      state.backend.liveStatus = payload;
      renderBackendPanels();
      if (showToast) toast("Live readiness refreshed.");
      return payload;
    } catch (err) {
      setStatus(`Live status failed: ${apiErrorMessage(err)}`, "error");
      if (showToast) toast(apiErrorMessage(err));
      return null;
    }
  }

  function renderLiveExecutionPanel() {
    const status = state.backend.liveStatus || activeData().live || {};
    const bitunix = status.bitunix || {};
    const preview = state.backend.livePreview;
    const list = $("#liveStatusList");
    if (list) {
      list.innerHTML = [
        compactRow("Live readiness", status.readiness_satisfied ? "Global live-readiness signoff is satisfied." : "Global live-readiness signoff is missing.", [{ label: status.readiness_satisfied ? "ready" : "locked", tone: status.readiness_satisfied ? "good" : "warn" }]),
        compactRow("Bitunix credentials", bitunix.credentials_configured ? "API key and secret are configured." : "Bitunix API credentials are not configured.", [{ label: bitunix.credentials_configured ? "configured" : "missing", tone: bitunix.credentials_configured ? "good" : "warn" }]),
        compactRow("Bitunix execution", bitunix.live_execution_enabled ? "Live order route is armed by env flags." : "Live execution env gate is off.", [{ label: bitunix.live_execution_enabled ? "armed" : "disabled", tone: bitunix.live_execution_enabled ? "warn" : "good" }]),
        compactRow("Bitunix leverage", `${bitunix.change_leverage_endpoint || "/api/v1/futures/account/change_leverage"} · max ${bitunix.max_configurable_leverage || 200}x`),
        compactRow("Confirmation", `Submit requires ${status.manual_order_confirmation_phrase || "PLACE LIVE ORDER"}.`),
        compactRow("Latest preview", preview ? `${preview.preview_id || "no id"} · safe=${Boolean(preview.preview?.live_order_safe)}` : "No live preview ticket yet."),
      ].join("");
    }
    const gate = $("#liveExecutionGateState"); if (gate) gate.textContent = bitunix.live_execution_enabled ? "armed" : "locked";
    if (!preview) setJson("liveOrderPreviewJson", status || {});
  }

  function buildLiveSignalPayload() {
    const plan = signalFromGuardianPlan();
    const ticket = buildTicketPayload();
    const payload = plan ? { ...plan, ...ticket } : { ...ticket };
    payload.exchange = "bitunix";
    payload.market_type = "futures";
    payload.symbol = rawSymbol(payload.symbol || currentSymbol());
    payload.leverage = Math.max(1, Math.min(200, Math.round(safeNumber(payload.leverage, 1))));
    payload.futures_risk_config = { max_leverage: String(payload.leverage), min_liquidation_buffer_pct: "0" };
    const chartPrice = latestChartPriceFor(payload.symbol);
    if (!payload.price && Number.isFinite(chartPrice)) payload.price = round(chartPrice, 8);
    if (safeArray(payload.take_profit_targets).length > 1) payload.take_profit_targets = [{ ...payload.take_profit_targets[0], close_pct: "100" }];
    return payload;
  }

  async function previewLiveOrderFromTicket() {
    const payload = buildLiveSignalPayload();
    try {
      const result = await api("/guardian/live/preview", { method: "POST", body: { signal: payload } });
      state.backend.livePreview = result;
      state.backend.livePreviewId = result.preview_id;
      const idInput = $("#livePreviewIdInput"); if (idInput) idInput.value = result.preview_id || "";
      setJson("ticketJsonPreview", { live_preview: result, signal: payload });
      setJson("liveOrderPreviewJson", result);
      setStatus(result.preview?.live_order_safe ? "Live Bitunix preview is safe according to current gates." : "Live preview returned locked/unsafe reasons.", result.preview?.live_order_safe ? "ok" : "warn");
      renderBackendPanels();
    } catch (err) {
      setJson("liveOrderPreviewJson", { signal: payload, error: apiErrorMessage(err) });
      setStatus(`Live preview failed: ${apiErrorMessage(err)}`, "error");
    }
  }

  async function submitLiveOrderFromPreview() {
    const previewId = $("#livePreviewIdInput")?.value || state.backend.livePreviewId || state.backend.livePreview?.preview_id;
    const confirmation = $("#liveConfirmInput")?.value || "";
    try {
      const result = await api("/guardian/live/submit", { method: "POST", body: { preview_id: previewId, confirmation } });
      setJson("liveOrderPreviewJson", result);
      setJson("ticketJsonPreview", result);
      setStatus("Live order submission request reached Bitunix REST client.", "warn");
      await refreshBackendState(false);
    } catch (err) {
      setJson("liveOrderPreviewJson", { preview_id: previewId, error: apiErrorMessage(err) });
      setStatus(`Live submit blocked: ${apiErrorMessage(err)}`, "error");
    }
  }

  function scheduleDrawingPersist() {
    if (!state.backend.data) return;
    clearTimeout(state.backend.drawingSavePending);
    state.backend.drawingSavePending = setTimeout(() => saveServerDrawings(false), 1200);
  }

  async function saveServerDrawings(showToast = true) {
    try {
      const payload = await api("/guardian/drawings", { method: "POST", body: { symbol: drawingSymbol(), drawings: state.drawings } });
      state.backend.serverDrawings = payload;
      renderDrawingsPanel();
      if (showToast) toast("Drawings saved to Sentinel server storage.");
      setStatus(`Saved ${payload.count ?? state.drawings.length} server drawings for ${payload.symbol || drawingSymbol()}.`, "ok");
    } catch (err) {
      setStatus(`Server drawing save failed: ${apiErrorMessage(err)}`, "error");
      if (showToast) toast(apiErrorMessage(err));
    }
  }

  async function loadServerDrawings(showToast = true, apply = true) {
    try {
      const payload = await api(`/guardian/drawings?symbol=${encodeURIComponent(drawingSymbol())}`);
      state.backend.serverDrawings = payload;
      if (apply) { state.drawings = safeArray(payload.drawings); updateAll({ keepChart: true }); }
      else renderDrawingsPanel();
      if (showToast) toast(`Loaded ${safeArray(payload.drawings).length} server drawings.`);
      return payload;
    } catch (err) {
      setStatus(`Server drawing load failed: ${apiErrorMessage(err)}`, "error");
      if (showToast) toast(apiErrorMessage(err));
      return null;
    }
  }

  async function deleteServerDrawings() {
    try {
      const payload = await api(`/guardian/drawings?symbol=${encodeURIComponent(drawingSymbol())}`, { method: "DELETE" });
      state.backend.serverDrawings = payload;
      state.drawings = [];
      updateAll({ keepChart: true });
      toast("Server drawings deleted.");
    } catch (err) { setStatus(`Server drawing delete failed: ${apiErrorMessage(err)}`, "error"); }
  }

  function stopEdgeStream() {
    if (state.backend.edgeStream) state.backend.edgeStream.close();
    state.backend.edgeStream = null;
    state.backend.edgeConnected = false;
  }

  function startEdgeStream() {
    stopEdgeStream();
    const ws = new WebSocket(wsUrl("/guardian/ws/edge"));
    state.backend.edgeStream = ws;
    ws.onopen = () => { state.backend.edgeConnected = true; setStatus("Guardian Edge stream connected.", "ok"); renderGlobalStatus(); renderDataPanel(); };
    ws.onclose = () => { state.backend.edgeConnected = false; renderGlobalStatus(); renderDataPanel(); };
    ws.onerror = () => setStatus("Guardian Edge stream error.", "error");
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        state.backend.edgeEventCount += 1;
        if (payload.event === "edge_snapshot" && payload.snapshot) {
          state.backend.edgeLatest = { snapshots: [payload.snapshot], count: 1, stream: "/guardian/ws/edge" };
          if (Array.isArray(payload.snapshot.series)) {
            setCurrentSymbol(payload.snapshot.symbol || currentSymbol());
            state.edge = payload.snapshot;
            state.candles = edgeToCandles(payload.snapshot);
            markCandleSeries(payload.snapshot.symbol || currentSymbol(), currentTimeframe(), "edge-stream");
            updateAll();
            syncMarkPriceFromChart();
          }
        } else if (payload.event === "connected" && payload.snapshots) state.backend.edgeLatest = payload.snapshots;
        renderGlobalStatus(); renderDataPanel();
      } catch (err) { setStatus(`Edge stream message failed: ${apiErrorMessage(err)}`, "error"); }
    };
  }

  async function publishEdgeSample() {
    try {
      const payload = await api("/guardian/edge/snapshot", { method: "POST", body: EDGE_HEATMAP_SAMPLE });
      state.backend.edgeLatest = { snapshots: [payload.snapshot], count: 1, stream: "/guardian/ws/edge" };
      loadEdge();
      renderDataPanel();
      setStatus("Published Edge sample snapshot to Guardian stream cache.", "ok");
    } catch (err) { setStatus(`Publish Edge sample failed: ${apiErrorMessage(err)}`, "error"); }
  }

  function stopCandleStream() {
    if (state.backend.candleStream) state.backend.candleStream.close();
    state.backend.candleStream = null;
    state.backend.candleConnected = false;
  }

  function startCandleStream() {
    stopCandleStream();
    const symbol = rawSymbol(currentSymbol());
    const interval = currentTimeframe();
    const limit = clamp(Math.round(safeNumber($("#barsInput")?.value, 180)), 80, 420);
    const ws = new WebSocket(wsUrl("/guardian/ws/candles", { symbol, interval, transport: "bitunix_ws", limit }));
    state.backend.candleStream = ws;
    markCandleSeries(symbol, interval, "stream");
    ws.onopen = () => { if (state.backend.candleStream !== ws) return; state.backend.candleConnected = true; setStatus(`Candle stream connected for ${symbol} ${interval}.`, "ok"); renderGlobalStatus(); renderDataPanel(); };
    ws.onclose = () => { if (state.backend.candleStream !== ws) return; state.backend.candleConnected = false; renderGlobalStatus(); renderDataPanel(); };
    ws.onerror = () => { if (state.backend.candleStream === ws) setStatus("Candle WebSocket error.", "error"); };
    ws.onmessage = (event) => {
      if (state.backend.candleStream !== ws) return;
      try {
        const payload = JSON.parse(event.data);
        state.backend.candleEventCount += 1;
        if (payload.event === "snapshot") {
          const candles = normalizeIncomingCandles(payload.candles);
          if (candles.length) {
            state.edge = null;
            state.candles = candles;
            markCandleSeries(symbol, interval, "stream");
            updateAll();
            syncMarkPriceFromChart();
          }
        } else if (payload.event === "candle" && payload.candle) upsertLiveCandle(payload.candle);
        else if (payload.event === "warning") setStatus(payload.detail || "Candle stream warning.", "warn");
        renderGlobalStatus(); renderDataPanel();
      } catch (err) { setStatus(`Candle stream message failed: ${apiErrorMessage(err)}`, "error"); }
    };
  }

  function stopStreams() {
    stopEdgeStream(); stopCandleStream();
    setStatus("Guardian streams disconnected.", "warn");
    renderGlobalStatus(); renderDataPanel();
  }

  function switchView(panel) {
    $$(".rail-item").forEach(b => b.classList.toggle("active", b.dataset.panel === panel));
    $$(".view-panel").forEach(v => v.classList.toggle("active", v.dataset.view === panel));
    if (panel === "chart") setTimeout(renderChart, 40);
    renderBackendPanels();
  }

  function setAutoRefresh(enabled) {
    state.backend.autoRefreshEnabled = enabled;
    if (state.backend.autoRefreshTimer) {
      clearInterval(state.backend.autoRefreshTimer);
      state.backend.autoRefreshTimer = null;
    }
    if (enabled) state.backend.autoRefreshTimer = setInterval(() => refreshBackendState(false), 10000);
    const btn = $("#autoRefreshBtn");
    if (btn) { btn.textContent = enabled ? "On" : "10s"; btn.setAttribute("aria-pressed", String(enabled)); btn.classList.toggle("active", enabled); }
    setStatus(enabled ? "Auto-refresh enabled every 10 seconds." : "Auto-refresh disabled.", enabled ? "ok" : "");
  }

  async function haltOrResume(action) {
    try {
      const body = action === "halt" ? { reason: $("#haltReasonInput")?.value || "guardian manual halt" } : {};
      const result = await api(action === "halt" ? "/control/halt" : "/control/resume", { method: "POST", body });
      setStatus(action === "halt" ? `Global halt active: ${result.reason || body.reason}` : "Trading engine resumed.", action === "halt" ? "warn" : "ok");
      await refreshBackendState(false);
    } catch (err) { setStatus(`${action} failed: ${err.message || err}`, "error"); }
  }

  function wireEvents() {
    $("#loadLive DataBtn").addEventListener("click", () => loadLive Data());
    $("#loadVcpBtn").addEventListener("click", loadVCP);
    $("#loadEdgeBtn").addEventListener("click", loadEdge);
    $("#autoBracketBtn").addEventListener("click", autoSafeBracket);
    $("#applyBracketBtn").addEventListener("click", applyInputsToBracket);
    $("#lastCloseBtn").addEventListener("click", () => {
      const last = state.candles.at(-1);
      if (!last) return;
      setBracket($("#sideInput").value, last.close, null, null, null, state.candles.length - 1);
    });
    $("#lockPlanBtn").addEventListener("click", () => {
      state.locked = !state.locked;
      $("#lockPlanBtn").textContent = state.locked ? "Unlock" : "Lock";
      $("#bracketState").textContent = state.locked ? "locked" : "unlocked";
      toast(state.locked ? "Plan locked." : "Plan unlocked.");
    });
    $("#copyPlanBtn").addEventListener("click", () => copyText($("#planJson").textContent).then(() => toast("Plan JSON copied.")));
    $("#exportBtn").addEventListener("click", exportPlanFile);
    $("#refreshBtn").addEventListener("click", () => loadLive Data());
    $("#themeBtn").addEventListener("click", () => {
      state.themeRoyal = !state.themeRoyal;
      document.documentElement.dataset.theme = state.themeRoyal ? "royal" : "guardian";
      renderChart();
    });
    $("#clearDrawingsBtn").addEventListener("click", () => { state.drawings = []; updateAll({ keepChart: true }); scheduleDrawingPersist(); toast("Manual drawings cleared."); });
    $("#resetBracketBtn").addEventListener("click", () => { state.bracket = null; state.locked = false; $("#lockPlanBtn").textContent = "Lock"; $("#bracketState").textContent = "unlocked"; updateAll({ keepChart: true }); toast("Bracket reset."); });
    $$(".tool-btn[data-tool]").forEach(btn => btn.addEventListener("click", () => setTool(btn.dataset.tool)));
    $$(".layer-toggle").forEach(box => box.addEventListener("change", () => { state.layers[box.dataset.layer] = box.checked; renderChart(); }));
    ["equityInput", "riskPctInput", "leverageInput", "feeBpsInput", "orderStyleInput"].forEach(id => $("#" + id).addEventListener("input", () => updateAll({ keepChart: true })));
    ["entryInput", "stopInput", "tp1Input", "tp2Input", "sideInput"].forEach(id => $("#" + id).addEventListener("change", applyInputsToBracket));
    $$(".rail-item").forEach(btn => btn.addEventListener("click", () => switchView(btn.dataset.panel || "chart")));
    const bindClick = (id, fn) => { const el = $("#" + id); if (el) el.addEventListener("click", fn); };
    const bindInput = (id, fn) => { const el = $("#" + id); if (el) el.addEventListener("input", fn); };
    const bindChange = (id, fn) => { const el = $("#" + id); if (el) el.addEventListener("change", fn); };
    bindClick("guardianRefreshBtn", () => refreshBackendState(true));
    bindClick("autoRefreshBtn", () => setAutoRefresh(!state.backend.autoRefreshEnabled));
    bindClick("haltBtn", () => haltOrResume("halt"));
    bindClick("resumeBtn", () => haltOrResume("resume"));
    bindClick("sampleSignalBtn", () => { const el = $("#signalTextInput"); if (el) el.value = sampleSignalText(); parseSignalTextFromUi(); });
    bindClick("parseSignalBtn", parseSignalTextFromUi);
    bindClick("previewSignalBtn", previewSignalTextFromUi);
    bindClick("submitTextSignalBtn", submitSignalTextFromUi);
    bindClick("copySignalPayloadBtn", () => copyText($("#signalPayloadPreview")?.textContent || "{}").then(() => toast("Signal payload copied.")));
    bindInput("signalSearchInput", renderSignalsPanel);
    bindClick("loadPlanToTicketBtn", () => { const payload = signalFromGuardianPlan(); if (payload) { populateTicketFromPayload(payload); setStatus("Guardian plan loaded into Trading Desk.", "ok"); } else toast("Draw a Guardian bracket first."); });
    bindClick("saveDraftBtn", () => { writeLocalJson("sentinelGuardianTicketDraft", buildTicketPayload()); toast("Ticket draft saved locally."); });
    bindClick("forgetDraftBtn", () => { window.localStorage?.removeItem("sentinelGuardianTicketDraft"); state.backend.ticketPayload = null; state.backend.ticketPreview = null; renderDeskPanel(); toast("Ticket draft forgotten."); });
    bindClick("buildTicketBtn", () => { const payload = buildTicketPayload(); state.backend.ticketPayload = payload; setJson("ticketJsonPreview", { alert: ticketAlertText(payload), payload }); renderDeskPanel(); setStatus("Ticket alert built locally.", "ok"); });
    bindClick("previewTicketBtn", previewTicketPayload);
    bindClick("submitTicketBtn", submitTicketPayload);
    bindClick("copyTicketAlertBtn", () => copyText(ticketAlertText(buildTicketPayload())).then(() => toast("Ticket alert copied.")));
    bindClick("copyTicketJsonBtn", () => copyText(jsonBlock(buildTicketPayload())).then(() => toast("Ticket JSON copied.")));
    bindClick("previewLiveOrderBtn", previewLiveOrderFromTicket);
    bindClick("submitLiveOrderBtn", submitLiveOrderFromPreview);
    bindClick("previewMarkBtn", () => previewOrApplyMark(false));
    bindClick("applyMarkBtn", () => previewOrApplyMark(true));
    bindInput("deskSearchInput", renderDeskTable);
    bindClick("previewFuturesRiskBtn", previewFuturesRisk);
    bindClick("refreshBracketsBtn", () => refreshBackendState(true));
    bindClick("exportStateBtn", () => downloadText(`sentinel-guardian-state-${Date.now()}.json`, jsonBlock(activeData())));
    bindClick("vcpBuildTicketBtn", () => { loadVCP(); setTimeout(() => { const payload = signalFromGuardianPlan(); if (payload) { payload.strategy_id = "guardian_vcp_breakout"; populateTicketFromPayload(payload); switchView("desk"); } }, 90); });
    bindClick("vcpAnalyzeBtn", () => quickAnalyzeFromPlan("vcpAnalyzePreview"));
    bindClick("vcpLoadLive DataBtn", () => { loadVCP(); switchView("vcp"); });
    bindClick("activateTrendToolBtn", () => { setTool("trend"); switchView("chart"); });
    bindClick("activateHorizontalToolBtn", () => { setTool("horizontal"); switchView("chart"); });
    bindClick("activateZoneToolBtn", () => { setTool("zone"); switchView("chart"); });
    bindClick("copyDrawingsBtn", () => copyText(jsonBlock(state.drawings)).then(() => toast("Drawings copied.")));
    bindClick("clearDrawingsLabBtn", () => { state.drawings = []; updateAll({ keepChart: true }); scheduleDrawingPersist(); toast("Drawings cleared."); });
    bindClick("saveServerDrawingsBtn", () => saveServerDrawings(true));
    bindClick("loadServerDrawingsBtn", () => loadServerDrawings(true, true));
    bindClick("deleteServerDrawingsBtn", deleteServerDrawings);
    bindClick("refreshStrategiesBtn", () => refreshBackendState(true));
    bindInput("strategySearchInput", renderStrategiesPanel);
    bindChange("strategyFilterInput", renderStrategiesPanel);
    bindChange("strategySortInput", renderStrategiesPanel);
    bindClick("refreshVenuesBtn", () => refreshBackendState(true));
    bindInput("exchangeSearchInput", renderExchangesPanel);
    bindClick("loadBitunixTickersBtn", loadBitunixTickers);
    bindClick("checkBitunixAccountBtn", checkBitunixAccount);
    bindClick("copyVenueJsonBtn", () => copyText($("#venueJsonPreview")?.textContent || "{}").then(() => toast("Venue JSON copied.")));
    bindClick("refreshLiveStatusBtn", () => loadLiveStatus(true));
    bindClick("venuePreviewLiveBtn", previewLiveOrderFromTicket);
    bindClick("warRoomLive DataBtn", warRoomLive Data);
    bindClick("warRoomAnalyzeBtn", warRoomAnalyze);
    bindClick("warRoomTicketBtn", warRoomTicket);
    bindClick("warRoomAnalyzeBtn", warRoomAnalyze);
    bindClick("warRoomCopyCandlesBtn", () => copyText(jsonBlock(guardianCandlesForApi())).then(() => toast("Current candles copied.")));
    bindClick("warRoomSubmitSignalBtn", submitWarRoomSignal);
    bindInput("auditSearchInput", renderAuditPanel);
    bindChange("auditFilterInput", renderAuditPanel);
    bindClick("refreshAuditBtn", () => refreshBackendState(true));
    bindClick("exportAuditCsvBtn", exportAuditCsv);
    bindClick("openDataDialogBtn", () => $("#dataDialog")?.showModal());
    bindClick("loadBitunixCandlesBtn", loadBitunixCandles);
    bindClick("startCandleStreamBtn", startCandleStream);
    bindClick("startEdgeStreamBtn", startEdgeStream);
    bindClick("publishEdgeSampleBtn", publishEdgeSample);
    bindClick("stopStreamsBtn", stopStreams);
    bindClick("loadEdgePanelBtn", () => { loadEdge(); switchView("chart"); });
    bindClick("copyCurrentCandlesBtn", () => copyText(jsonBlock(guardianCandlesForApi())).then(() => toast("Current candles copied.")));
    bindClick("loadPanelDataBtn", loadPanelPastedData);
    $$(".quick-symbol").forEach(btn => btn.addEventListener("click", () => selectDeskSymbol(btn.dataset.symbol)));
    $$(".ticket-tf").forEach(btn => btn.addEventListener("click", () => { $("#timeframeInput").value = btn.dataset.tf; loadLive Data(); }));
    $$(".size-preset").forEach(btn => btn.addEventListener("click", () => { const cap = safeNumber(activeData().risk?.max_order_notional, 100); const remaining = Math.max(0, cap - safeNumber(activeData().account?.open_notional, 0)); const v = btn.dataset.size === "max" ? cap : btn.dataset.size === "remaining" ? remaining : btn.dataset.size; if ($("#ticketSizeInput")) $("#ticketSizeInput").value = String(v); renderDeskPanel(); }));
    $$(".mini-tab[data-desk-table]").forEach(btn => btn.addEventListener("click", () => { state.backend.deskTable = btn.dataset.deskTable; $$(".mini-tab[data-desk-table]").forEach(b => b.classList.toggle("active", b === btn)); renderDeskTable(); }));
    document.addEventListener("click", (event) => {
      const target = event.target.closest("button");
      if (!target) return;
      if (target.dataset.approvalApprove) approveSignal(target.dataset.approvalApprove);
      if (target.dataset.approvalReject) rejectSignal(target.dataset.approvalReject);
      if (target.dataset.loadSignalTicket) {
        const s = activeSignals().find(x => x.signal_id === target.dataset.loadSignalTicket);
        if (s) { populateTicketFromPayload(s); switchView("desk"); }
      }
      if (target.dataset.bracketAction) bracketAction(target.dataset.signalId, target.dataset.bracketAction);
      if (target.dataset.pinStrategy) {
        const pins = new Set(state.backend.strategyPins || []);
        pins.has(target.dataset.pinStrategy) ? pins.delete(target.dataset.pinStrategy) : pins.add(target.dataset.pinStrategy);
        state.backend.strategyPins = [...pins]; writeLocalJson("sentinelGuardianPinnedStrategies", state.backend.strategyPins); renderStrategiesPanel();
      }
      if (target.dataset.loadStrategyTicket) loadStrategyTicket(target.dataset.loadStrategyTicket);
      if (target.dataset.analysisStrategy) analysisStrategy(target.dataset.analysisStrategy);
      if (target.dataset.previewStrategy) previewStrategy(target.dataset.previewStrategy);
      if (target.dataset.venueCapabilities) loadVenueJson(target.dataset.venueCapabilities, "capabilities");
      if (target.dataset.venueIntegration) loadVenueJson(target.dataset.venueIntegration, "integration");
      if (target.dataset.venueStatus) loadVenueJson(target.dataset.venueStatus, "status");
      if (target.dataset.auditInspect) { try { setJson("warRoomJsonPreview", JSON.parse(target.dataset.auditInspect)); switchView("warroom"); } catch { /* noop */ } }
      if (target.dataset.inspectOrder) { const order = activeOrders().find(o => String(o.signal_id || o.order_id || o.id) === target.dataset.inspectOrder); setJson("ticketJsonPreview", order || {}); switchView("desk"); }
      if (target.dataset.inspectPosition) { const position = activePositions().find(o => String(o.symbol || "") === target.dataset.inspectPosition); setJson("ticketJsonPreview", position || {}); switchView("desk"); }
    });
    $("#loadPastedBtn").addEventListener("click", () => {
      try {
        const candles = parsePastedData($("#dataInput").value);
        if (candles.length < 20) throw new Error("Need at least 20 valid candles.");
        state.edge = null;
        state.candles = candles;
        markCandleSeries(currentSymbol(), currentTimeframe(), "manual");
        state.drawings = [];
        state.bracket = null;
        $("#dataDialog").close();
        updateAll();
        syncMarkPriceFromChart();
        toast(`Loaded ${candles.length} candles.`);
      } catch (err) {
        toast(err.message || String(err));
      }
    });
    const canvas = $("#chartCanvas");
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointerleave", () => { state.hover = null; renderChart(); });
    window.addEventListener("resize", () => renderChart());
    window.addEventListener("keydown", (event) => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
      const key = event.key.toLowerCase();
      if (key === "1") setTool("long");
      if (key === "2") setTool("short");
      if (key === "t") setTool("trend");
      if (key === "h") setTool("horizontal");
      if (key === "z") setTool("zone");
      if (key === "e") setTool("eraser");
      if (key === "escape") setTool("cursor");
    });
    setInterval(() => {
      const now = new Date();
      $("#clockTime").textContent = now.toLocaleTimeString([], { hour12: false });
    }, 1000);
  }

  function init() {
    wireEvents();
    const draft = readLocalJson("sentinelGuardianTicketDraft", null);
    if (draft) state.backend.ticketPayload = draft;
    loadLive Data("volatile");
    if (draft) setTimeout(() => populateTicketFromPayload(draft), 40);
    setTimeout(autoSafeBracket, 80);
    setTimeout(() => refreshBackendState(false), 150);
  }

  init();
})();
