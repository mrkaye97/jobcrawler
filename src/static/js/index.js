function createCompanyRow(company) {
    const row = document.createElement('tr');
    row.dataset.id = company.id;

    const nameCell = document.createElement('td');
    const boardUrlCell = document.createElement('td');
    const jobPostingUrlCell = document.createElement('td');


    const scrapingMethodCell = document.createElement('td');
    let scrapingMethodSelect;

    if ("{{ current_user.email }}" === "mrkaye97@gmail.com") {
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

    if ("{{ current_user.email }}" === "mrkaye97@gmail.com") {
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

    if ("{{ current_user.email }}" === "mrkaye97@gmail.com") {
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

function createBoardRow(board) {
    const row = document.createElement('tr');
    row.dataset.id = board.search_id;

    const companyNameCell = document.createElement('td');
    const companySelect = document.createElement('select');
    const searchCell = document.createElement('td');

    companies.forEach(company => {
        const option = document.createElement('option');
        option.value = company.id;
        option.text = company.name;

        if (company.id === board.company_id) {
            option.selected = true;
        }
        companySelect.appendChild(option);
    });

    companyNameCell.appendChild(companySelect);

    searchCell.contentEditable = true;

    searchCell.innerText = board.search_regex;

    row.appendChild(companyNameCell);
    row.appendChild(searchCell);

    const actionsCell = document.createElement('td');
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-danger';

    deleteBtn.innerText = 'Delete';
    deleteBtn.addEventListener('click', function () {
        fetch(`/searches/${row.dataset.id}`, {
            method: 'DELETE'
        }).then(() => {
            row.remove();
        });
    });

    actionsCell.appendChild(deleteBtn);
    row.appendChild(actionsCell);

    companySelect.addEventListener('change', autoSaveBoard);
    searchCell.addEventListener('blur', autoSaveBoard);
    searchCell.addEventListener('keydown', handleEnterKey(autoSaveBoard));

    return row;
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

function populateCompanySelect() {
    const companySelect = document.getElementById('company-select');

    console.log(companies);
    // Clear existing options
    companySelect.innerHTML = '';

    companies.forEach(company => {
        console.log("Company from in populateCompanySelect", company);
        const option = document.createElement('option');
        option.value = company.id;
        option.text = company.name;
        companySelect.appendChild(option);
    });
}

function createJobSearchCard(companyId, searches) {
    // The card container
    const cardDiv = document.createElement('div');
    cardDiv.className = 'col';
    cardDiv.dataset.id = companyId;

    // The card element
    const card = document.createElement('div');
    card.className = 'card h-100';

    // Card body
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    // Card title
    const cardTitle = document.createElement('h5');
    cardTitle.className = 'card-title';
    cardTitle.textContent = companies.find(c => c.id === companyId).name;
    cardBody.appendChild(cardTitle);

    // Card content (search links)
    const searchList = document.createElement('ul');
    searches.forEach(search => {
        const listItem = document.createElement('li');
        listItem.textContent = search.search_regex;
        listItem.dataset.searchId = search.search_id;

        // Add delete button to list item
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-danger btn-sm ms-2';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', function () {
            fetch(`/searches/${listItem.dataset.searchId}`, {
                method: 'DELETE'
            }).then(() => {
                listItem.remove();
            });
        });
        listItem.appendChild(deleteBtn);

        searchList.appendChild(listItem);
    });
    cardBody.appendChild(searchList);

    card.appendChild(cardBody);
    cardDiv.appendChild(card);

    return cardDiv;
}

function createBoardCard(board) {
    const colDiv = document.createElement('div');
    colDiv.className = 'col';

    const cardDiv = document.createElement('div');
    cardDiv.className = 'card github-card';

    const cardTitle = document.createElement('h4');
    cardTitle.textContent = board.companyName;
    cardDiv.appendChild(cardTitle);

    const searchList = document.createElement('ul');
    board.searches.forEach(search => {
        const listItem = document.createElement('li');
        listItem.textContent = search.search_regex;
        searchList.appendChild(listItem);
    });
    cardDiv.appendChild(searchList);

    const deleteBtn = document.createElement('a');
    deleteBtn.className = 'card-btn';
    deleteBtn.textContent = 'Delete';
    deleteBtn.href = '#';
    // Update the event listener with the new delete functionality
    deleteBtn.addEventListener('click', function (event) {
        event.preventDefault();
        // Delete the company and all searches associated with it
    });
    cardDiv.appendChild(deleteBtn);

    colDiv.appendChild(cardDiv);

    return colDiv;
}