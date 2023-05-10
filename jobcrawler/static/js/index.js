function createCompanyRow(company, email) {
    const row = document.createElement('tr');
    row.dataset.id = company.id;

    const nameCell = document.createElement('td');
    const boardUrlCell = document.createElement('td');
    const jobPostingUrlCell = document.createElement('td');


    const scrapingMethodCell = document.createElement('td');
    let scrapingMethodSelect;

    if (email === "mrkaye97@gmail.com") {
        scrapingMethodSelect = document.createElement('select');
        const soupOption = document.createElement('option');
        const seleniumOption = document.createElement('option');

        soupOption.value = 'soup';
        soupOption.text = 'Soup';
        seleniumOption.value = 'selenium';
        seleniumOption.text = 'Selenium';

        scrapingMethodSelect.appendChild(soupOption);
        scrapingMethodSelect.appendChild(seleniumOption);
        scrapingMethodSelect.value = company.scraping_method;

        scrapingMethodCell.appendChild(scrapingMethodSelect);
    } else {
        const scrapingMethodText = document.createElement('span');
        scrapingMethodText.innerText = company.scraping_method === 'soup' ? 'Soup' : 'Selenium';
        scrapingMethodCell.appendChild(scrapingMethodText);
    }

    if (email === "mrkaye97@gmail.com") {
        nameCell.contentEditable = true;
        boardUrlCell.contentEditable = true;
        jobPostingUrlCell.contentEditable = true;
    }

    jobPostingUrlCell.innerText = company.job_posting_url_prefix || '';
    nameCell.innerText = company.name;
    boardUrlCell.innerText = company.board_url;

    row.appendChild(nameCell);
    row.appendChild(boardUrlCell);
    row.appendChild(jobPostingUrlCell);
    row.appendChild(scrapingMethodCell);

    if (email === "mrkaye97@gmail.com") {
        const actionsCell = document.createElement('td');
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-danger';

        deleteBtn.innerText = 'Delete';
        deleteBtn.addEventListener('click', function () {
            fetch(`/companies/${row.dataset.id}`, {
                method: 'DELETE'
            }).then(() => {
                row.remove();
            });
        });

        actionsCell.appendChild(deleteBtn);
        row.appendChild(actionsCell);

        nameCell.addEventListener('blur', autoSaveCompany);
        nameCell.addEventListener('keydown', handleEnterKey(autoSaveCompany));
        boardUrlCell.addEventListener('blur', autoSaveCompany);
        boardUrlCell.addEventListener('keydown', handleEnterKey(autoSaveCompany));
        jobPostingUrlCell.addEventListener('blur', autoSaveCompany);
        jobPostingUrlCell.addEventListener('keydown', handleEnterKey(autoSaveCompany));

        if (scrapingMethodSelect) {
            scrapingMethodSelect.addEventListener('change', autoSaveCompany);
        }
    }

    return row;
}

function autoSaveCompany(event) {
    const cell = event.target;
    const row = cell.closest('tr');
    const nameCell = row.querySelector('td:nth-child(1)');
    const boardUrlCell = row.querySelector('td:nth-child(2)');
    const jobPostingUrlCell = row.querySelector('td:nth-child(3)');
    const scrapingMethodSelect = row.querySelector('td:nth-child(4) select');

    const formData = new FormData();

    formData.append('name', nameCell.innerText);
    formData.append('board_url', boardUrlCell.innerText);
    formData.append('job_posting_url_prefix', jobPostingUrlCell.innerText);
    formData.append('scraping_method', scrapingMethodSelect.value);

    fetch(`/companies/${row.dataset.id}`, {
        method: 'PUT',
        body: formData
    });
}

function createBoardCard(search, companies) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    const cardTitle = document.createElement('h5');
    cardTitle.className = 'card-title';

    cardTitle.textContent = companies.find(c => c.id === parseInt(search.company_id)).name;

    const cardText = document.createElement('p');
    cardText.className = 'card-text';
    cardText.textContent = search.search_regex;

    cardBody.appendChild(cardTitle);
    cardBody.appendChild(cardText);
    cardDiv.appendChild(cardBody);
    cardDiv.dataset.id = search.search_id;

    cardDiv.addEventListener('click', function () {
        editMode = true;
        fetch(`/searches/${search.search_id}`)
            .then(response => response.json())
            .then(updatedSearch => {
                companyNameSelect.innerHTML = '';
                companies.forEach(company => {
                    const option = document.createElement('option');
                    option.value = company.id;
                    option.text = company.name;
                    if (company.id === updatedSearch.company_id) {
                        option.selected = true;
                    }
                    companyNameSelect.appendChild(option);
                });

                const searchText = document.getElementById('search-text');
                searchText.value = updatedSearch.search_regex;

                $('#addRowModal').modal('show');
            });
    });


    return cardDiv;
}

function autoSaveBoard(event) {
    const cell = event.target;
    const row = cell.closest('tr');
    const companySelect = row.querySelector('td:nth-child(1) select');
    const searchCell = row.querySelector('td:nth-child(2)');

    const formData = new FormData();
    formData.append('company_id', companySelect.value);
    formData.append('search_regex', searchCell.innerText);

    fetch(`/searches/${row.dataset.id}`, {
        method: 'PUT',
        body: formData
    });
}


function handleEnterKey(saveFunction) {
    return function (event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent adding a newline
            event.target.blur(); // Remove focus from the cell
        }
    };
}

function runCrawlJob() {
    fetch('/scraping/run-crawl-job', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}

function runEmailJob() {
    fetch('/scraping/run-email-job', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}
