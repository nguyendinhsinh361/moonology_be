#!/bin/bash

# Run isort to sort imports
echo "Running isort..."
isort app/

# Run black to format code
echo "Running black..."
black app/

# Run flake8 to check for errors
echo "Running flake8..."
flake8 app/

echo "Linting complete!" 