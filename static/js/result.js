document.addEventListener('DOMContentLoaded', function () {
    const fishModal = document.getElementById('fishModal');
    if (!fishModal) return;

    const canvas = document.getElementById('fishCanvas');
    const ctx = canvas.getContext('2d');
    let image = new Image();

    // Add a cross-origin attribute to the image to avoid canvas tainting issues
    // if the image is served from a different origin in the future.
    image.crossOrigin = "Anonymous";

    fishModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        
        const fishId = button.getAttribute('data-fish-id');
        const confidence = button.getAttribute('data-fish-confidence');
        const boxStr = button.getAttribute('data-fish-box');
        const imageUrl = button.getAttribute('data-fish-image');

        // Safely parse the box string
        let box;
        try {
            // The box string looks like [x1, y1, x2, y2]
            box = JSON.parse(boxStr.replace(/'/g, '"'));
        } catch (e) {
            console.error("Failed to parse bounding box data:", boxStr, e);
            return; // Don't open the modal if data is invalid
        }

        const modalFishId = document.getElementById('modalFishId');
        const modalFishConfidence = document.getElementById('modalFishConfidence');
        const modalFishBox = document.getElementById('modalFishBox');
        
        // Use the translation keys passed from the template
        const fishText = fishModal.dataset.fishText || 'Fish';
        
        modalFishId.textContent = `${fishText} #${fishId}`;
        modalFishConfidence.textContent = confidence;
        modalFishBox.textContent = `[${box.join(', ')}]`;

        image.onload = function() {
            // Set canvas size based on image aspect ratio to prevent distortion
            const aspectRatio = image.naturalWidth / image.naturalHeight;
            const canvasContainer = canvas.parentElement;
            let canvasWidth = canvasContainer.clientWidth;
            let canvasHeight = canvasWidth / aspectRatio;

            // If the calculated height is too large for the viewport, adjust
            const maxHeight = window.innerHeight * 0.7;
            if (canvasHeight > maxHeight) {
                canvasHeight = maxHeight;
                canvasWidth = canvasHeight * aspectRatio;
            }

            canvas.width = canvasWidth;
            canvas.height = canvasHeight;

            // Calculate scaling factors
            const scaleX = canvas.width / image.naturalWidth;
            const scaleY = canvas.height / image.naturalHeight;

            // Draw the full image on the canvas
            ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

            // Highlight the selected fish
            const [x1, y1, x2, y2] = box;
            const rectX = x1 * scaleX;
            const rectY = y1 * scaleY;
            const rectWidth = (x2 - x1) * scaleX;
            const rectHeight = (y2 - y1) * scaleY;

            // Draw a semi-transparent overlay on the rest of the image
            ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // "Cut out" the highlighted rectangle from the overlay by clearing it
            ctx.clearRect(rectX, rectY, rectWidth, rectHeight);
            
            // Redraw the highlighted part of the image to make it appear bright
            ctx.drawImage(image, x1, y1, x2 - x1, y2 - y1, rectX, rectY, rectWidth, rectHeight);

            // Draw a border around the highlighted fish
            ctx.strokeStyle = '#007aff'; // Apple's primary blue
            ctx.lineWidth = 3;
            ctx.strokeRect(rectX, rectY, rectWidth, rectHeight);
        };
        
        // Set the image source. This will trigger the onload event.
        if (image.src !== imageUrl) {
            image.src = imageUrl;
        } else {
            // If the image is already loaded (e.g., clicking another fish), just redraw the canvas
            image.onload();
        }
    });

    // Clear canvas when modal is hidden to prevent showing old data
    fishModal.addEventListener('hide.bs.modal', function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    });
});
