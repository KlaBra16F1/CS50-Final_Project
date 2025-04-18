// Script for 'make-test.html'
// Compensates for multi-select on this page
var subtopics_loaded;
let topic = document.querySelector('#topic');
topic.addEventListener('change', async function() {
    subtopics_loaded = false;
    let res = await fetch('/get-subtopics?t_id=' + topic.value);
    document.querySelector('#subtopic').innerHTML = '';
    let subtopics = await res.json();
    if (subtopics["empty"] == 200) {
        return
    }
    let html = '';
    for (s of subtopics) {
        html += '<option value="' + s.s_id + '">' + s.subtopic + ' (' + s.count + ')</option>'
    }
    document.querySelector('#subtopic').innerHTML = html;
    subtopics_loaded = true;
});