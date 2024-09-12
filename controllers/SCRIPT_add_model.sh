#!/bin/bash

set -e

# 1. Input and validate model name:

printf "\nEnter model name (in dot-formatting): "
read model_name

if [ ! $model_name ]; then
    printf "Invalid model name, exit!\n\n"
    exit
fi

# (get model name with replaced dots)
model_name_u="${model_name//./_}"

# 2. Clone and rename template file (with overwriting confirmation):
new_file_name="model__${model_name_u}.py"
cp --interactive model__TEMPLATE.py ${new_file_name}
printf "Created new model file: ${new_file_name}\n"

# 3. Replace all substrings "model.name" and "model_name" in new file:
sed -i "s/model\.name/${model_name}/g" ${new_file_name}
sed -i "s/model_name/${model_name_u}/g" ${new_file_name}

# 4. Add import line in file 'resources.py':
echo "from . import model__${model_name_u}" >> resources.py
printf "New model file linked inside the file 'resources.py'\n"

printf "Success!\n\n"
