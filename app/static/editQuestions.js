let selector = document.querySelector("#topic-selector");
    selector.addEventListener('change', function(){
    getQuestions();
});

function getQuestions(){
    let t_id = document.querySelector('#topic').value;
    let s_id = document.querySelector('#subtopic').value;
    if (subtopics_loaded == false) {
        s_id = '';
    }
    var req = new XMLHttpRequest();
    req.onreadystatechange = function() {
        if (req.readyState == 4 && req.status == 200) {
            document.querySelector('#table').innerHTML = req.responseText;
        }
    };
    req.open('GET', '/get-questions?t_id='+ t_id +'&s_id=' + s_id, true);
    req.send();
    editable = undefined;
};

async function deleteQuestion(event) {
    let del = event.currentTarget.value;
    let req = await fetch('/edit-questions?delete=' + del);
    let res = await req.json();
    Metro.notify.create("Success",`Deleted ${res["questions"]} questions and ${res["answers"]} answers.`,{cls: 'success'});
    getQuestions();
};

async function sendUpdate(q_id, event){
    console.log(event)
    let question = event.srcElement[0].value;
    let multiple = event.srcElement[2].value;
    console.log('q:',question, 'm:', multiple);
    event.preventDefault();
    let req = await fetch('/edit-questions?update=' + q_id +"&question=" + question + "&multiple=" + multiple);
    let res = await req.json();
    Metro.notify.create("Success",`Updated ${res["changes()"]} question.`,{cls: 'success'});
    getQuestions();
    editable = undefined;
};

function update(id) {
    // prevent multiple call for update
    if (typeof(editable) !== 'undefined') {
            Metro.notify.create('Error','You can only edit one question at a time. Press ENTER to submit first.',{ cls: 'alert'})
            return;
    }
    editable = true;
    // Setting delay of 500 ms to compensate for lag in table-search
    setTimeout(function(){
        let tr = document.querySelector(`#q${id}`).parentElement.parentElement;
        let td = tr.getElementsByTagName('td')
        
        if (td[4].querySelector('p') == undefined) {
            td[4].querySelector('div').appendChild(document.createElement("p"));
        }
        let question = td[4].querySelector('p').innerHTML;
        let multiple = td[5].querySelector('input').value;
        // Make pre-selection based on previous entry
        let selected0 = '';
        let selectet1 = '';
        if (multiple == 1) {
            
            selectet1 = 'selected';
        } else {
            selected0 = 'selected';
        }
        let html = `
        <td>${td[2].innerHTML}</td>
        <td>${td[3].innerHTML}</td>
        <td colspan="2">
            <form onsubmit="sendUpdate(${id}, event);return false;">

                <label>Question</label>
                <input name="question" value="${question}" type="text" data-role="input" >
                <label>Multiple Choice</label>
                <select name="multiple" data-role="select" class="input-small w-25" data-filter="false">
                    <option value=0 ${selected0}>No</option>
                    <option value=1 ${selectet1}>Yes</option>
                </select>
            <button class="button success">Update</button>
            <button type="button" class="button" onclick="getQuestions();">Abort</button>

            </form>
        </td>
        <td>${td[6].innerHTML}</td>`
        tr.innerHTML = html;
    }, 500);
};