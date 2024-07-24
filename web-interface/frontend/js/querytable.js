document.addEventListener('DOMContentLoaded', function() {
    // Event listeners for sortable headers
    document.querySelectorAll('#metadataTable th.sortable').forEach((header) => {
        header.addEventListener('click', () => {
            const index = header.getAttribute('data-index');
            sortTable(parseInt(index, 10));
        });
    });

    // Event listeners for filterable headers
    document.querySelectorAll('#metadataTable th.filterable').forEach(header => {
        header.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleFilterBox(header);
        });
    });

    // Function to fetch images and metadata from the backend
    async function fetchData() {
        try {
            const response = await fetch('/api/uploaded_images');
            const data = await response.json();
            const imageList = data.images;

            const metadataPromises = imageList.map(async (filename) => {
                const metadataResponse = await fetch(`/api/metadata?filename=${filename}`);
                return await metadataResponse.json();
            });

            const metadataArray = await Promise.all(metadataPromises);
            return metadataArray;
        } catch (error) {
            console.error('Error fetching data:', error);
            return [];
        }
    }

    // Function to render the table
    function renderTable(data) {
        const tableBody = document.querySelector('#metadataTable tbody');
        tableBody.innerHTML = '';
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td><img src="backend/uploaded_images/${item.filename}" alt="${item.filename}" width="50" class="clickable-image"></td>
                <td>${item.filename}</td>
                <td><button class="prompt-button" data-prompt="${item.prompt}">Prompt</button></td>
                <td>${item.user}</td>
                <td>${item.timestamp}</td>
                <td>${item.quality}</td>
                <td>${item.style}</td>
                <td>${item.model}</td>
                <td>${item.size}</td>
            `;
            tableBody.appendChild(row);
        });

        // Reattach event listeners
        document.querySelectorAll('.clickable-image').forEach(img => {
            img.addEventListener('click', () => openImagePopup(img.src));
        });
        document.querySelectorAll('.prompt-button').forEach(button => {
            button.addEventListener('click', (e) => openPromptPopup(e.target.getAttribute('data-prompt')));
        });
    }

    // Initial fetch and render
    fetchData().then(data => {
        renderTable(data);
    });

    // Sorting function
    function sortTable(columnIndex) {
        const table = document.getElementById('metadataTable');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.rows);
        const currentDirection = table.getAttribute('data-sort-direction');
        const currentColumn = table.getAttribute('data-sort-column');
        let isAscending = true;

        if (currentColumn == columnIndex) {
            isAscending = currentDirection !== 'ascending';
        } else {
            isAscending = true;
        }

        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];

            let aText = aCell.textContent.trim();
            let bText = bCell.textContent.trim();

            // Handle sorting for numeric values
            if (!isNaN(aText) && !isNaN(bText)) {
                aText = parseFloat(aText);
                bText = parseFloat(bText);
                return isAscending ? aText - bText : bText - aText;
            }

            // Default sorting for strings
            return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
        });

        tbody.innerHTML = '';
        tbody.append(...rows);

        table.setAttribute('data-sort-column', columnIndex);
        table.setAttribute('data-sort-direction', isAscending ? 'ascending' : 'descending');

        document.querySelectorAll('#metadataTable th').forEach(th => th.classList.remove('asc', 'desc'));
        document.querySelectorAll('#metadataTable th')[columnIndex].classList.toggle('asc', isAscending);
        document.querySelectorAll('#metadataTable th')[columnIndex].classList.toggle('desc', !isAscending);
    }

    // Filter box functionality
    function toggleFilterBox(header) {
        const column = header.getAttribute('data-column');
        const filterBox = document.getElementById(`filter-${column}`);
        const rect = header.getBoundingClientRect();

        if (filterBox.style.display === 'none' || !filterBox.style.display) {
            filterBox.style.display = 'block';
            filterBox.style.top = `${rect.bottom}px`;
            filterBox.style.left = `${rect.left}px`;
            populateFilterBox(column, filterBox);
        } else {
            filterBox.style.display = 'none';
        }
    }

    function populateFilterBox(column, filterBox) {
        const uniqueValues = [...new Set(data.map(item => item[column]))];
        filterBox.innerHTML = uniqueValues.map(value => `
            <label>
                <input type="checkbox" value="${value}" onchange="filterTable('${column}')">
                ${value} (${data.filter(item => item[column] === value).length})
            </label>
        `).join('');
    }

    function filterTable(column) {
        const checkboxes = document.querySelectorAll(`#filter-${column} input[type="checkbox"]`);
        const checkedValues = [...checkboxes].filter(cb => cb.checked).map(cb => cb.value);

        const filteredData = data.filter(item => checkedValues.length === 0 || checkedValues.includes(item[column]));
        renderTable(filteredData); // Re-render table and reattach event listeners
    }

    // Search functionality
    document.getElementById('searchInput').addEventListener('input', function () {
        const query = this.value.toLowerCase();
        const filteredData = data.filter(item => 
            Object.values(item).some(value => value.toString().toLowerCase().includes(query))
        );
        renderTable(filteredData);
    });

    // Show popup with prompt text
    function openPromptPopup(prompt) {
        const promptPopup = document.getElementById('promptPopup');
        const promptText = document.getElementById('promptText');
        promptText.textContent = prompt;
        promptPopup.style.display = 'block';
    }

    // Show popup with enlarged image
    function openImagePopup(imageSrc) {
        const imagePopup = document.getElementById('imagePopup');
        const enlargedImage = document.getElementById('enlargedImage');
        enlargedImage.src = imageSrc;
        imagePopup.style.display = 'block';
    }

    // Close popup functions
    function closePopup(popupId) {
        document.getElementById(popupId).style.display = 'none';
    }

    // Event listeners for closing popups
    document.querySelector('.popup .close-button').addEventListener('click', () => {
        closePopup('promptPopup');
    });

    window.addEventListener('click', (event) => {
        if (event.target === document.getElementById('promptPopup')) {
            closePopup('promptPopup');
        }
    });

    document.querySelector('.popup .close-button').addEventListener('click', () => {
        closePopup('imagePopup');
    });

    window.addEventListener('click', (event) => {
        if (event.target === document.getElementById('imagePopup')) {
            closePopup('imagePopup');
        }
    });

    // Function to close all filter boxes
    function closeAllFilterBoxes() {
        document.querySelectorAll('.filter-box').forEach(filterBox => {
            filterBox.style.display = 'none';
        });
    }

    // Event listener to close filter boxes when clicking outside
    document.addEventListener('click', (event) => {
        const target = event.target;

        // Check if the click is outside any filter box or filter header
        const filterBoxes = document.querySelectorAll('.filter-box');
        const filterHeaders = document.querySelectorAll('#metadataTable th.filterable');

        let clickedInsideFilterBox = false;

        filterBoxes.forEach(box => {
            if (box.contains(target)) {
                clickedInsideFilterBox = true;
            }
        });

        filterHeaders.forEach(header => {
            if (header.contains(target)) {
                clickedInsideFilterBox = true;
            }
        });

        // If the click is outside all filter boxes, close them
        if (!clickedInsideFilterBox) {
            closeAllFilterBoxes();
        }
    });
});