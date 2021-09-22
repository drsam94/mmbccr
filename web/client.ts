

class Requester {
    // TODO: figure out the type of this input

    private uploadFile(ev: any) {
        const req = new XMLHttpRequest();
        // Because the internet is stupid, this has to be POST in order for the body
        // to be sent
        req.open("POST", "http://ec2-3-143-141-13.us-east-2.compute.amazonaws.com:8000/");
        req.responseType = "blob";
        const output = document.getElementById("output") as HTMLDivElement;
        req.onload = function (evt: Event) {
            const url = window.URL.createObjectURL(req.response);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            // For some reason the http implementation requires this to be lowercase even
            // if it was not serialized as such
            const seedHdr = "seed";
            // We check the existence first to workaround some silly behavior where
            // Chrome 'refuses' to read the header otherwise
            console.log(req.getAllResponseHeaders());
            const seed = req.getAllResponseHeaders().indexOf(seedHdr) >= 0 ? req.getResponseHeader(seedHdr) : 0;
            a.download = "MegaMan_BattleChip_Challenge_" + seed + ".gba";
            document.body.appendChild(a);
            a.click();
            const text = a.download + " downloaded";
            console.log(text);
            output.innerHTML = text;
        };
        req.onerror = function () {
            output.innerHTML = "An error occurred trying to connect to the server";
        };
        if (!ev.target) {
            return;
        }

        const fileBuffer = ev.target.result as ArrayBuffer;
        const elem = document.getElementById("confData") as HTMLTextAreaElement;
        const confText = elem.value;
        const encoder = new TextEncoder();
        const confBuffer = encoder.encode(confText);
        const body = new Uint8Array(fileBuffer.byteLength + confBuffer.byteLength);
        body.set(new Uint8Array(confBuffer), 0);
        body.set(new Uint8Array(fileBuffer), confBuffer.byteLength);
        req.setRequestHeader("ConfLength", confBuffer.byteLength.toString());
        const seedElem = document.getElementById("seedInput") as HTMLInputElement;
        if (seedElem.value !== "0") {
            req.setRequestHeader("Seed", seedElem.value);
        }
        output.innerHTML = "Sending request to randomize...";
        req.send(body.buffer);
    }
    public readInputFile(ev: Event) {
        if (!ev.target) {
            return;
        }
        const input = ev.target as HTMLInputElement;
        if (!input.files) {
            return;
        }
        const file = input.files[0];
        if (!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = this.uploadFile;
        reader.readAsArrayBuffer(file);
    }
};

function getDefaultConfText() {
    return `[ChipRange]
ap = 100
hp = 10
mb = 0

[NaviRange]
ap = 100
hp = 0
mb = 50

[ChipGlobal]
preserveOrdering = true

[Encounters]
randomizeChips = true
randomizeNavi = false
smartAtkPlus = true
fillChips = true
shuffle = false
randomizeOperators = true
upgradeChipParam = 0.5

[Names]
randomizeNames = false`.replace(/\n/i, "\r\n");
}

function createIntroDOM() {
    const header = document.createElement("h1");
    header.innerText = "Meagman Battlechip Challenge Randomizer";

    const introText = document.createElement("p");
    introText.innerHTML = `
Welcome to the web interface of the MMBCR. </br>
You may upload your own file here to then download a randomized ROM with the </br>
provided seed an conf. For documentation on how the conf works or to file buf reports </br>
or ask questions, see the  <a href="https://github.com/drsam94/mmbccr">github repository</a> for the project</br>
Note that there are some features of the command line interface not available in the interface, </br>
such as the ability to specify a list of chip names to randomize among. </br>
Note that the server is currently run on an amazon aws ec2 instance with nearly no care </br>
taken to long term stability; that pay improve over time, but the CLI will always work!`;

    document.body.appendChild(header);
    document.body.appendChild(introText);
}
function main() {
    createIntroDOM();
    const req = new Requester();
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.id = "filePicker";
    fileInput.addEventListener<"change">("change", (ev) => { req.readInputFile(ev); }, false);
    const label = document.createElement("label");
    label.htmlFor = fileInput.id;
    label.innerText = "Upload Megaman Battle Chip Challenge English ROM";

    const textInput = document.createElement("textarea");
    textInput.rows = 25;
    textInput.cols = 80;
    textInput.id = "confData";
    textInput.value = getDefaultConfText();

    const seedInput = document.createElement("input");
    seedInput.type = "text";
    seedInput.value = "0";
    seedInput.id = "seedInput";

    const seedLabel = document.createElement("label");
    seedLabel.htmlFor = seedInput.id;
    seedLabel.innerText = "Set Seed";

    const outputDiv = document.createElement("div");
    outputDiv.innerHTML = "No file chosen yet";
    outputDiv.id = "output";
    document.body.appendChild(label);
    document.body.appendChild(fileInput);
    document.body.appendChild(outputDiv);
    document.body.appendChild(document.createElement("br"));
    document.body.appendChild(seedLabel);
    document.body.appendChild(seedInput);
    document.body.appendChild(document.createElement("br"));
    document.body.appendChild(textInput);
}

document.body.onload = main;