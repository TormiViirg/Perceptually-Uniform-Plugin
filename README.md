# Perceptually-Uniform-Plugin

Pistikprogramm olemasolevale graafikatarkvarale, mis aitab kasutajal valida värvitooni eraldiseisva muutujana, mõjutamata seejuures teisi värviomadusi, kasutades selleks kaasaegseid värviteooria lähenemisi ja põhimõtteid. Töö käigus disainitakse ja arendatakse tööriistu, mis arvestavad tajuliselt ühtlaste värviruumide eripärade ja võimalustega.

Repository koosneb hetkel kahest peamisest osast. Tööriistadest, mis on vajalikud varasemate ja autori poolt loodud värvivaliku tööriistade võrdluseks ja algoritmist, mis otsustab millised värvid kasutajaliideses kuvatakse. Lõpufaasides lisandub kolmas osa mis sisaldab algoritmi sisaldavat pistikuprogrammi ennast vastava kasutajaliidesega.

## Lahendatav probleem

Praegu puuduvad disaineritel tõhusad ja intuitiivsed tööriistad, mis võimaldaksid värvitooni valida või muuta ilma teisi värviomadusi mõjutamata ja vastupidi värvimudelis peamistes graafilise disaini tarkvarades. Selle tulemusel võivad muudatused, mis kasutaja eeldusel mõjutavad vaid värvitooni, tajutavalt muuta ka värvi heledust või küllastust. See lahkheli inimtaju ja mudeli vahel muudab värviga töötamise disainiprojektides ebatäpseks, puudulikuks värvide valiku osas ja aeganõudvaks. Sellest tulenevalt käituvad ka genereeritud värviüleminekud värvivaliku tööriistade kasutajaliideses etteennustamatult.

<img width="749" height="619" alt="image" src="https://github.com/user-attachments/assets/bdfcfbce-4769-47b8-84d5-2bd7b8a02b11" />
Allikas: https://bottosson.github.io/posts/oklab/

Probleemi süvendab ka värviruumide kohati liigselt detailne värvide eraldusvõime, mis on ühtlane kogu kaetavas ulatuses. Tulenevalt sellest, et nägemissüsteem on jällegi ebaühtlane värvide eristamisvõimes ja eristab mõndasid värvi piirkondi kõrgema eraldusvõimega kui teisi, on automaatselt genereeritud värviüleminek, kasutaja vaatepildist kasutajaliideses kallutatud just ebaolulistele värvide suunas, selle asemel, et just suurendada oluliste osakaalu vähem oluliste arvelt tajupõhiselt ühtlase jaotuseni jõudmiseks või isegi tahtlikult raskesti eristatavate värvide alaesindadamiseks. Mis tähendab, et detailsust vajavad piirkonnad on esindatud sama osakaaluga kui need, mis seda ei vaja, mis viib olukorrani kus kõrgema bitti sagedusega värviruumide puhul on värve mida kasutaja ei saa kasutajaliideses valida oma töö raames kasutamiseks, olgugi, et monitor on võimeline neid kuvama. Selline naivistlik lähenemine pole jätkusuutlik raisatud ekraaniruumi tõttu, eriti kõrgema bit-i sagedusega ekraanide puhul. Tulenevalt asjaolust, et tegemist on pistikprogrammiga peab värvivaliku tööriist ka ideaalis mahtuma selleks kasutajaliideses varasemalt ettemääratud piirkonda.

<img width="530" height="589" alt="Group 42 (6)" src="https://github.com/user-attachments/assets/528b390a-8112-4744-951f-f1536e3ba157" />

Siis on veel hunnik väikseid asju nagu võimalus värviruumi piirkondi tööks välja valida ja salvestada tiimiliikmetega jagatavas formaadis, kus on võimalik värvidele kirjeldusi lisada, näiteks brändi värvide puhul. Võimaldab sisse ostetud arenduse kallal töötavatel disaineritel näha kasutajaliidese tasemel lubatud värve ja konteksti kus neid kasutada tohib rakenduse siseselt.

<img width="749" height="490" alt="image" src="https://github.com/user-attachments/assets/66ed768e-d409-4541-a91b-6257ffdd8984" />

Allikas: https://www.figma.com/files/team/1362368493098064381/resources/community/file/912837788133317724

Eyedropper tööriist võimaldab mitut värvi korraga valida ja paletti lisada. Sisse ehitatud värviharmoonia soovitused tajupõhiselt ühtlase värviruumi põhjal.

Võrdlus kahe teise varasema värvimudeliga <img width="327" height="200" alt="image" src="https://github.com/user-attachments/assets/895b306f-ade0-47cd-a20a-cb20ee4e96bb" />

Allikas: https://evannorton.github.io/Acerolas-Epic-Color-Palettes/


## Algoritm ja kasutajaliides:

Eemaldame värvid mida inimsilm teistest värvidest eristada ei suuda kasutajaliideses. Selleks on hetkel plaaanis kasutada monitoride kvaliteedi kontrollis kasutusel olevaid valemeid, kirjutamise hetkel on kasutusel delta94 lihtuse huvides, aga hiljem on plaanis kasutada kaasaegsemaid. Kirjutamise hetkel ei ole autor ühtegi kasutajaliidest leidnud, mis sellist väljajätu kriteeriumit kasutaks, levinum on lihtsalt värvi gradienti kasutada, healjuhul lab-i kasutades kui on soovi tajupõhisema katte järele.


Algne poolik disain:
<img width="2476" height="1296" alt="Group 209" src="https://github.com/user-attachments/assets/00f0418d-4e8b-4faa-a5db-36cf008e3094" />


Edasi toimub kasutajaliidese põhine filtreerimine heleduse põhjal. Hetkel on algoritmis kasutusel HSL lihtsuse jaoks, hiljem võetakse kasutusele tajupõhiselt ühtlasem OKLCH.

Seejärel prioritiseeritakse kasutajaliideses värvid, mis digimeedias ja graafika disainis kõige tihedamini kasutusel on läbi nende osakaalu suurendamise kasutaja liideses neile suurema pindala eraldades. Seda osa algoritmi veel listud pole.

Hetkel pole veel otsusele jõutud selles osas  kui agressiivselt tasub värve ja tausta ringi seada, et kasutajaliideses maksimaalne hulk värve eristatav oleks. Tegemist on olulise küsimusega kuna RGB värvimudel on nn liitev (additive) ja ilma kontekstita pole võimalik seal kõiki värve kuvada nt pruun. 
<img width="1016" height="921" alt="image" src="https://github.com/user-attachments/assets/0c8398be-55f0-4b73-8518-6fd8ad56f019" />

## Tööriistad:

### Veebiäpp kasutajaliideses olevate värvide analüüsiks ja csv formaati salvestamine hilisema statistika jaoks.

Tausta värvi muutmis võimalus, et väride erisusi paremini näha, algoritmi ja sRGB katte tööriista testimise jaoks.
<img width="1133" height="946" alt="image" src="https://github.com/user-attachments/assets/a95f9544-dc91-47e4-b4c7-6f0e53cef329" />
Pakub ülevaate sellest mitu ainulaadset värvi pikslit on ja mis värvi need on, nende osakaalu kasutajaliideses andmete valideerimiseks enne edasisi statistilisi toimetusi väljastatud csv faili alusel.
<img width="1389" height="972" alt="image" src="https://github.com/user-attachments/assets/a44414b5-b8dc-477d-bc5b-09df01adf061" />

### sRGB kattuvuse visualiseermis tööriist

Hetkel renderdab ekraanile kogu sRGB värvigamma ja loeb hiire all oleva värvi. Seda teeb hiire kordinaatide põhjal arvutades algse mappingu kordinaadi ja selle põhjal vastava värvi,mitte ekraanilt otse, kuna CORS ei luba. Lähipäevil lisandub csv failide laadimine ja võimalus sinna laetu salvestada bmp failina tööriista testimise ja andmeteagregeerimis eesmärgil. Rakendus näitab milline osa sRGB-st kaetud on visuaalsel viisil. 

<img width="1881" height="968" alt="image" src="https://github.com/user-attachments/assets/cc03774e-fca9-4c5a-885b-3583f8b3e03a" />

Kuna png, jpg jms pildi formaadid tekitaksid ise kompressiooni käigus täiendavaid värve olukorras kus on tarvilik saada täpne ülevaade sellest kui palju tööriistad sRGB värviruumist katavad ja millise osakaalu millised värvid moodustavad, oli täiendav töö tarvilik. Seetõttu oli vaja töötlemise käigus bmp faile kasutada ja tagada, et kogu tööriista ahel seda formaati toetaks. Mistõttu loodi terminalil põhinev windowsi rakendus bmp formaadis kuvatõmmiste tegemiseks. Algoritmi poolt loodud värvi swatchide puhul, mis salvestati eri valgus astmete juurest peale silmale eristamatute värvide eemaldamist, salvestati tulemus bmp formaadis analüüsiks. Värvi analüüsi veebirakenduses tagati tugi bmp failide üleslaadimiseks ja sRGB kattuvust illustreerivas rakenduses lisati genereeritud või üleslaetud csv failide poolt osaliselt täidetud värvikatte jäädvustamiseks bmp ekspordi tugi andmete ristvalideerimiseks.

Autor Tormi Viirg Tallinna Ülikooli Digitehnoloogiate instituut 
