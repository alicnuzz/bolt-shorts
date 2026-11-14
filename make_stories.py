"""Builds stories/*.json from compact definitions. Bolt opens and closes every story."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FOOT = " Follow Bolt for a new 'why' every day!"

def bolt(expr="neutral", pose="shrug", x=0.24, s=0.95):
    return {"outfit": "bolt", "x": x, "y": 0.95, "s": s, "expr": expr, "pose": pose, "talk": True}

def man(outfit="engineer", expr="neutral", pose="idle", x=0.7, s=0.95, talk=False):
    return {"outfit": outfit, "x": x, "y": 0.95, "s": s, "expr": expr, "pose": pose, "talk": talk}

def sc(text, landmark, terrain, time="day", chars=None, **kw):
    d = {"bg": "scene", "landmark": landmark, "terrain": terrain, "time": time, "text": text, "chars": chars or []}
    d.update(kw)
    return d

S = {}

S["02-white-pyramids"] = dict(
    title="The Pyramids Used to Be Shiny White! 🏜️ #shorts",
    desc="The Great Pyramid was once covered in polished white limestone that shone in the sun. So where did the shiny shell go?",
    tags=["great pyramid", "ancient egypt", "casing stones", "history facts", "did you know"],
    emph=["white", "shiny", "polished", "mirror", "earthquake", "cairo", "gone"],
    scenes=[
        sc("Why are the pyramids brown and bumpy, when they used to be shiny white?", "pyramids", "desert", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("When the Great Pyramid was finished, it was covered in smooth, polished white limestone.", "pyramids", "desert", "day"),
        sc("In the bright Egyptian sun, it would have glowed like a giant mirror in the desert.", "pyramids", "desert", "sunset", [man("kid", "shocked", "panic", x=0.75)]),
        sc("What we see today is only the rough inside.", "pyramids", "desert", "day"),
        sc("So where did the shiny shell go?", "sphinx", "desert", "day", [man("kid", "thinking", "shrug", x=0.78)], bubble="?"),
        sc("In 1303, a huge earthquake shook Egypt and loosened many of the casing stones.", "pyramids", "desert", "night", shake=True),
        sc("Builders in Cairo carried the fallen blocks away to build mosques and other buildings.", "bricks", "desert", "day", [man("engineer", "happy", "point", x=0.72)]),
        sc("Today, only a few of the original white stones are left near the base.", "pyramids", "desert", "dawn"),
        sc("So the pyramids didn't just get old. People recycled their shiny skin!" + FOOT, "pyramids", "desert", "sunset", [bolt("happy", "wave")]),
    ])

S["03-pisa-saved"] = dict(
    title="How Engineers Stopped the Leaning Tower From Falling 🏗️ #shorts",
    desc="By 1990 the Leaning Tower of Pisa was close to falling. Engineers saved it with a surprisingly simple trick: they dug.",
    tags=["leaning tower of pisa", "engineering", "italy", "how it works", "did you know"],
    emph=["falling", "closed", "soil", "north", "straightened", "200", "dig"],
    scenes=[
        sc("Why hasn't the Leaning Tower of Pisa fallen over yet?", "pisa", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("For hundreds of years, it leaned a little more every year.", "pisa", "grass", "sunset"),
        sc("By 1990, engineers were worried it could fall at any moment, so they closed it to visitors.", "pisa", "grass", "day", [man("engineer", "worried", "panic", x=0.75)], shake=True),
        sc("Pushing it back up would be too dangerous. So they tried something clever.", "pisa", "grass", "dawn", [man("engineer", "thinking", "think", x=0.75)]),
        sc("They slowly dug soil out from under the high side of the tower.", "pisa", "grass", "day", [man("engineer", "happy", "point", x=0.75)]),
        sc("Little by little, the ground sank on that side, and the tower leaned back.", "pisa", "grass", "sunset"),
        sc("By 2001, it had straightened by about 45 centimeters.", "pisa", "grass", "day", ding=True, ding_at=1.0),
        sc("Engineers think it should now stay safe for at least 200 years.", "pisa", "grass", "night"),
        sc("They saved it by digging, not by pushing!" + FOOT, "pisa", "grass", "day", [bolt("happy", "wave")]),
    ])

S["04-roman-concrete"] = dict(
    title="Why Roman Concrete Lasts 2,000 Years (And Ours Doesn't) 🏛️ #shorts",
    desc="Roman buildings and harbors have survived for 2,000 years. Scientists found that Roman concrete can actually heal its own cracks.",
    tags=["roman concrete", "ancient rome", "engineering", "science facts", "did you know"],
    emph=["2,000", "heal", "cracks", "lime", "seawater", "stronger", "crystals"],
    scenes=[
        sc("Why are Roman buildings still standing after 2,000 years, when modern concrete cracks in decades?", "colosseum", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("Scientists studied tiny white lumps of lime inside Roman concrete.", "temple", "grass", "day", [man("engineer", "thinking", "think", x=0.75)]),
        sc("They used to think the lumps were just sloppy mixing. They were wrong.", "temple", "grass", "sunset", [man("engineer", "shocked", "panic", x=0.75)]),
        sc("When a crack forms and rainwater gets in, the lime dissolves and fills the crack with new crystals.", "colosseum", "grass", "dawn"),
        sc("The concrete actually heals itself!", "colosseum", "grass", "day", ding=True, ding_at=0.4),
        sc("Roman harbors used volcanic ash, and seawater made them grow rare crystals that got stronger over time.", "lighthouse", "sea", "day"),
        sc("So the ocean that destroys our concrete was making theirs stronger.", "lighthouse", "sea", "sunset"),
        sc("Today, engineers are copying the Roman recipe." + FOOT, "colosseum", "grass", "day", [bolt("happy", "wave")]),
    ])

S["05-colosseum-holes"] = dict(
    title="Why the Colosseum Is Full of Holes 🧀 #shorts",
    desc="The Colosseum's walls are covered in strange holes. They weren't made by battles. They were made by people looking for metal.",
    tags=["colosseum", "ancient rome", "history facts", "middle ages", "did you know"],
    emph=["holes", "iron", "clamps", "metal", "300", "dug", "missing"],
    scenes=[
        sc("Why does the Colosseum look like it's covered in holes?", "colosseum", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("Cannonballs? Bullets? Nope.", "colosseum", "grass", "sunset", [man("kid", "shocked", "panic", x=0.76)]),
        sc("When the Romans built it, they held the big stone blocks together with iron clamps.", "colosseum", "grass", "day", [man("engineer", "happy", "point", x=0.75)]),
        sc("There were hundreds of tons of metal hidden inside the walls.", "colosseum", "grass", "dawn"),
        sc("Centuries later, after Rome fell, metal was very valuable.", "temple", "grass", "night"),
        sc("So people chipped into the stone to pull the clamps out and melt them down.", "colosseum", "grass", "day", [man("engineer", "angry", "point", x=0.74)], shake=True),
        sc("Every hole you see is where a piece of iron used to be.", "colosseum", "grass", "sunset", ding=True, ding_at=0.5),
        sc("The Colosseum wasn't shot. It was recycled!" + FOOT, "colosseum", "grass", "day", [bolt("happy", "wave")]),
    ])

S["06-wet-sand"] = dict(
    title="How Egyptians Moved Giant Stones With Water 💧 #shorts",
    desc="How did ancient Egyptians drag huge stones across the desert? Scientists found a simple trick: wet sand.",
    tags=["ancient egypt", "pyramids", "physics", "how it was built", "did you know"],
    emph=["water", "wet", "sand", "half", "painting", "sledge", "trick"],
    scenes=[
        sc("How did ancient Egyptians drag giant stones across the desert?", "pyramids", "desert", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("They put the stones on big wooden sledges and pulled them with ropes.", "pyramids", "desert", "day", [man("engineer", "worried", "point", x=0.74)]),
        sc("But on dry sand, a sledge digs in and piles sand in front of it. It's really hard to pull.", "pyramids", "desert", "sunset", [man("engineer", "angry", "panic", x=0.74)], shake=True),
        sc("In 2014, scientists tested something shown in an old Egyptian tomb painting.", "sphinx", "desert", "day"),
        sc("In the painting, a man pours water on the sand in front of the sledge.", "sphinx", "desert", "dawn", [man("kid", "thinking", "think", x=0.76)]),
        sc("They found that the right amount of water makes the sand firm, so the sledge slides instead of sinking.", "pyramids", "desert", "day", ding=True, ding_at=1.5),
        sc("That can cut the pulling force roughly in half!", "pyramids", "desert", "sunset", [man("engineer", "happy", "wave", x=0.74)]),
        sc("The secret tool was just a bucket of water." + FOOT, "pyramids", "desert", "day", [bolt("happy", "wave")]),
    ])

S["07-petra-bullets"] = dict(
    title="Why Petra's Treasury Is Covered in Bullet Holes 💰 #shorts",
    desc="The stone urn on top of Petra's Treasury is full of bullet marks. People thought a pharaoh's treasure was hidden inside.",
    tags=["petra", "jordan", "treasury", "legend", "did you know"],
    emph=["bullet", "treasure", "urn", "pharaoh", "solid", "nothing", "treasury"],
    scenes=[
        sc("Why is this ancient building in Jordan covered in bullet holes?", "petra", "desert", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("This is Al-Khazneh in Petra. Its name means The Treasury.", "petra", "desert", "day"),
        sc("At the very top, there's a big stone urn.", "petra", "desert", "sunset"),
        sc("Local legend said a pharaoh had hidden his gold inside it.", "petra", "desert", "night", [man("kid", "shocked", "panic", x=0.76)]),
        sc("So for years, people fired rifles at the urn, hoping to break it open and make the treasure rain down.", "petra", "desert", "day", shake=True),
        sc("But the urn is carved from solid rock. There was never anything inside.", "petra", "desert", "dawn", ding=True, ding_at=1.2),
        sc("The only treasure was the building itself." + FOOT, "petra", "desert", "day", [bolt("happy", "wave")]),
    ])

S["08-parthenon-explosion"] = dict(
    title="The Day the Parthenon Exploded 💥 #shorts",
    desc="The Parthenon stood almost perfectly for over 2,000 years. Then, in 1687, it was used to store gunpowder.",
    tags=["parthenon", "ancient greece", "athens", "history facts", "did you know"],
    emph=["2,000", "gunpowder", "1687", "cannonball", "exploded", "roof", "ruin"],
    scenes=[
        sc("Why is the Parthenon a ruin, when it survived almost perfectly for 2,000 years?", "temple", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("For centuries it was a temple, then a church, then a mosque. It still had its roof.", "temple", "grass", "sunset"),
        sc("In 1687, Athens was under attack, and the defenders stored gunpowder inside it.", "temple", "grass", "night", [man("sailor", "worried", "idle", x=0.76)]),
        sc("They hoped the enemy wouldn't fire at such a famous building.", "temple", "grass", "night"),
        sc("They were wrong. A cannonball hit the gunpowder.", "volcano", "grass", "night", shake=True),
        sc("The explosion blew off the roof and knocked down many of its columns.", "temple", "grass", "night", [man("kid", "shocked", "panic", x=0.76)], shake=True),
        sc("What took 2,000 years to wear down was ruined in a single second." + FOOT, "temple", "grass", "dawn", [bolt("worried", "shrug")]),
    ])

S["09-chichen-chirp"] = dict(
    title="This Pyramid Chirps Like a Bird When You Clap 👏 #shorts",
    desc="Clap your hands in front of El Castillo at Chichén Itzá and the echo comes back sounding like a bird's chirp.",
    tags=["chichen itza", "maya", "mexico", "acoustics", "did you know"],
    emph=["clap", "chirp", "bird", "echo", "quetzal", "stairs", "sacred"],
    scenes=[
        sc("What happens if you clap your hands in front of this pyramid?", "mayan", "jungle", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("This is El Castillo at Chichén Itzá in Mexico, built by the Maya.", "mayan", "jungle", "day"),
        sc("If you stand at the bottom and clap, the echo comes back as a strange chirp.", "mayan", "jungle", "sunset", [man("kid", "happy", "panic", x=0.76)], ding=True, ding_at=1.0),
        sc("The sound bounces off the steps one by one, so the echo slides down in pitch.", "mayan", "jungle", "dawn"),
        sc("To many listeners, it sounds like the call of the quetzal, a bird that was sacred to the Maya.", "mayan", "jungle", "day", fx=["birds"]),
        sc("Was it on purpose? Some scientists think so. Others say it's a happy accident.", "mayan", "jungle", "sunset", [man("engineer", "thinking", "think", x=0.75)]),
        sc("Either way, the pyramid still sings back to visitors today." + FOOT, "mayan", "jungle", "night", [bolt("happy", "wave")], fx=["fireflies"]),
    ])

S["10-moai-hats"] = dict(
    title="Why Some Easter Island Heads Wear Red Hats 🗿 #shorts",
    desc="Some moai on Easter Island wear giant red stone hats called pukao. How did people lift them up there?",
    tags=["easter island", "moai", "rapa nui", "ancient mystery", "did you know"],
    emph=["red", "hats", "pukao", "tons", "rolled", "ramp", "volcano"],
    scenes=[
        sc("Why do some Easter Island statues wear giant red hats?", "moai", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("They're called pukao, and they're carved from red volcanic stone.", "moai", "grass", "sunset"),
        sc("It all came from one quarry on the island, a crater called Puna Pau.", "volcano", "grass", "day"),
        sc("Some of these hats weigh as much as two elephants!", "moai", "grass", "day", [man("kid", "shocked", "panic", x=0.76)]),
        sc("So how did the Rapa Nui people get them on top of the statues?", "moai", "grass", "dawn", bubble="?", chars=[man("kid", "thinking", "shrug", x=0.7)]),
        sc("Scientists think they rolled the hats up a ramp, then tipped them into place.", "moai", "grass", "day", [man("engineer", "happy", "point", x=0.75)], ding=True, ding_at=1.5),
        sc("The red color may have shown the importance of the ancestors the statues honor.", "moai", "grass", "sunset"),
        sc("Hats off to some seriously clever engineers!" + FOOT, "moai", "grass", "day", [bolt("happy", "wave")]),
    ])

S["11-inca-walls"] = dict(
    title="Why Inca Walls Survive Earthquakes That Destroy Modern Buildings 🌋 #shorts",
    desc="Peru has strong earthquakes, but Inca walls at Machu Picchu have stood for centuries. Their secret is in the shape.",
    tags=["machu picchu", "inca", "engineering", "earthquakes", "did you know"],
    emph=["earthquakes", "mortar", "dance", "trapezoid", "lean", "perfectly", "centuries"],
    scenes=[
        sc("Why do Inca walls survive earthquakes that knock down modern buildings?", "terraces", "mountains", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("Peru has lots of strong earthquakes.", "terraces", "mountains", "sunset", shake=True),
        sc("But the best Inca walls used no mortar at all. The stones were cut to fit together perfectly.", "terraces", "mountains", "day", [man("engineer", "happy", "point", x=0.75)]),
        sc("When the ground shakes, the stones can jiggle a little, then settle back into place.", "terraces", "mountains", "dawn", shake=True),
        sc("People say the stones dance.", "terraces", "mountains", "day", ding=True, ding_at=0.5),
        sc("The walls also lean slightly inward, and the doors and windows are shaped like trapezoids, which are much more stable.", "terraces", "mountains", "sunset"),
        sc("That's why these walls are still standing after centuries." + FOOT, "terraces", "mountains", "day", [bolt("happy", "wave")]),
    ])

S["12-angkor-west"] = dict(
    title="Why Angkor Wat Faces the Wrong Way 🧭 #shorts",
    desc="Almost every temple at Angkor faces east, toward the sunrise. Angkor Wat faces west. Here's why historians think that is.",
    tags=["angkor wat", "cambodia", "temples", "history facts", "did you know"],
    emph=["west", "east", "sunrise", "sunset", "tomb", "king", "equinox"],
    scenes=[
        sc("Why does Angkor Wat face the wrong way?", "angkor", "jungle", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("Almost all the temples around Angkor face east, toward the rising sun.", "angkor", "jungle", "dawn"),
        sc("But Angkor Wat, the biggest of them all, faces west.", "angkor", "jungle", "sunset", [man("kid", "shocked", "panic", x=0.76)]),
        sc("In Hindu tradition, the west is linked with the setting sun and with death.", "angkor", "jungle", "sunset"),
        sc("So many historians think Angkor Wat was built as the tomb temple of its king, Suryavarman the Second.", "angkor", "jungle", "night", fx=["fireflies"]),
        sc("And there's another surprise. On the spring equinox, the sun rises right over the central tower.", "angkor", "jungle", "dawn", ding=True, ding_at=1.8),
        sc("Facing west lets visitors at the entrance watch it happen." + FOOT, "angkor", "jungle", "day", [bolt("happy", "wave")]),
    ])

S["13-hagia-dome"] = dict(
    title="Hagia Sophia's Dome Fell Down... So They Built It Taller 🕌 #shorts",
    desc="Just 21 years after Hagia Sophia was finished, its giant dome collapsed. The builders' answer surprised everyone.",
    tags=["hagia sophia", "istanbul", "byzantine", "engineering", "did you know"],
    emph=["collapsed", "earthquakes", "taller", "537", "558", "dome", "steeper"],
    scenes=[
        sc("Why does Hagia Sophia's dome look taller than it was first built?", "hagia", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("Hagia Sophia was finished in the year 537, with the biggest dome anyone had ever seen.", "hagia", "grass", "sunset"),
        sc("But Constantinople had earthquakes, and the walls holding the dome were slowly pushed outward.", "hagia", "grass", "night", shake=True),
        sc("In 558, just 21 years later, the dome came crashing down.", "hagia", "grass", "night", [man("kid", "shocked", "panic", x=0.76)], shake=True),
        sc("Instead of giving up, builders made a new dome that was taller and steeper.", "hagia", "grass", "dawn", [man("engineer", "happy", "point", x=0.75)]),
        sc("A steeper dome pushes down more and out less, so it's easier for the walls to hold.", "hagia", "grass", "day", ding=True, ding_at=1.5),
        sc("That rebuilt dome has now stood for almost 1,500 years." + FOOT, "hagia", "grass", "sunset", [bolt("happy", "wave")]),
    ])

S["14-ulugh-beg"] = dict(
    title="The Giant Underground Star Ruler of Samarkand 🌌 #shorts",
    desc="Ulugh Beg built an observatory in Samarkand with a giant curved stone track to measure the stars. It was lost for centuries.",
    tags=["ulugh beg", "samarkand", "uzbekistan", "astronomy", "did you know"],
    emph=["stars", "observatory", "giant", "1908", "underground", "1,000", "year"],
    scenes=[
        sc("How did a ruler in Samarkand measure the stars without a telescope?", "madrasa", "desert", "night", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("About 600 years ago, Ulugh Beg ruled Samarkand. He also loved astronomy.", "madrasa", "desert", "day"),
        sc("He built a huge observatory on a hill, with a giant curved stone track built into the ground.", "madrasa", "desert", "sunset", [man("engineer", "happy", "point", x=0.75)]),
        sc("It was about 40 meters in radius, so astronomers could measure the positions of stars very precisely.", "madrasa", "desert", "night"),
        sc("His team made a catalog of over 1,000 stars, and measured the length of a year almost perfectly.", "madrasa", "desert", "night", ding=True, ding_at=1.0),
        sc("After he died, the observatory was destroyed and forgotten.", "madrasa", "desert", "dawn", [man("kid", "worried", "idle", x=0.76)]),
        sc("Then, in 1908, an archaeologist dug on the hill and found the underground part of the giant track.", "madrasa", "desert", "day", [man("engineer", "shocked", "panic", x=0.74)]),
        sc("You can still visit it in Samarkand today." + FOOT, "madrasa", "desert", "night", [bolt("happy", "wave")]),
    ])

S["15-terracotta-colors"] = dict(
    title="The Terracotta Army Lost Its Colors in Minutes 🎨 #shorts",
    desc="The Terracotta warriors look gray, but they were once painted in bright colors. When they were dug up, the paint flaked off in minutes.",
    tags=["terracotta army", "china", "archaeology", "history facts", "did you know"],
    emph=["colors", "painted", "minutes", "air", "flaked", "gray", "bright"],
    scenes=[
        sc("Why are the Terracotta warriors gray?", "soldiers", "grass", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1),
        sc("They weren't always. More than 2,200 years ago, they were painted in bright reds, blues, and greens.", "soldiers", "grass", "sunset"),
        sc("Underground, the damp soil kept the paint stuck on.", "soldiers", "grass", "night"),
        sc("But when archaeologists dug them up, the dry air hit the paint.", "soldiers", "grass", "day", [man("engineer", "worried", "idle", x=0.75)]),
        sc("The paint curled up and flaked off, sometimes in just a few minutes.", "soldiers", "grass", "day", [man("engineer", "shocked", "panic", x=0.75)], shake=True),
        sc("That's one reason archaeologists still haven't opened the emperor's tomb itself.", "soldiers", "grass", "dawn", ding=True, ding_at=1.0),
        sc("They want to wait until they can protect what's inside." + FOOT, "soldiers", "grass", "day", [bolt("happy", "wave")]),
    ])

S["16-nazca-straight"] = dict(
    title="How the Nazca Lines Were Drawn Without Seeing Them 📏 #shorts",
    desc="The Nazca Lines are perfect giant drawings in the desert. How did people make them without seeing them from the sky?",
    tags=["nazca lines", "peru", "ancient mystery", "how it was made", "did you know"],
    emph=["straight", "stakes", "rope", "giant", "grid", "copied", "simple"],
    scenes=[
        sc("How did people draw giant pictures they could only see from the sky?", "nazca", "desert", "day", [bolt("thinking", "shrug")], ding=True, ding_at=0.1, near=False),
        sc("The Nazca Lines in Peru include a hummingbird, a monkey, and lines that run straight for kilometers.", "nazca", "desert", "day", near=False),
        sc("Some people think aliens must have helped. But there's a much simpler answer.", "nazca", "desert", "sunset", [man("kid", "shocked", "panic", x=0.76)], near=False),
        sc("Wooden stakes have been found at the ends of some lines.", "nazca", "desert", "day", [man("engineer", "thinking", "think", x=0.75)], near=False),
        sc("With stakes and rope, you can lay out very straight lines and scale up a small drawing using a simple grid.", "nazca", "desert", "dawn", [man("engineer", "happy", "point", x=0.75)], near=False, ding=True, ding_at=2.0),
        sc("In 1982, a small team used only wooden stakes and string and made a giant copy of one figure in a couple of days.", "nazca", "desert", "day", near=False),
        sc("No aliens needed, just clever people with rope!" + FOOT, "nazca", "desert", "sunset", [bolt("happy", "wave")], near=False),
    ])

if __name__ == "__main__":
    out = os.path.join(HERE, "stories")
    os.makedirs(out, exist_ok=True)
    for k, v in S.items():
        v["id"] = k
        with open(os.path.join(out, k + ".json"), "w", encoding="utf-8") as f:
            json.dump(v, f, indent=1, ensure_ascii=False)
    print(len(S), "stories written")
