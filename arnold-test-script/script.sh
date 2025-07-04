#!/bin/bash

# File to modify
FILE="data.txt"

# Function to generate a random time between 9:00 and 18:00
random_time() {
    hour=$(( RANDOM % 10 + 9 ))  # 9 to 18
    minute=$(( RANDOM % 60 ))
    second=$(( RANDOM % 60 ))
    printf "%02d:%02d:%02d" $hour $minute $second
}

# Create 20 commits over the last 2 weeks
for i in {1..10}; do
    # Random number of days ago (0-13 for past 2 weeks)
    days_ago=$(( RANDOM % 2 ))
    
    # Generate date string
    commit_date="$(date -d "-${days_ago} days" "+%Y-%m-%d") $(random_time)"
    
    # Update the file
    echo "Update $i: $commit_date" > $FILE
    
    # Add and commit with the backdated timestamp
    git add $FILE
    GIT_AUTHOR_DATE="$commit_date" GIT_COMMITTER_DATE="$commit_date" git commit -m "Commit $i of 10"
    
    echo "Autocommit with script for date: $commit_date"
done

# Push all commits
git push origin main || git push origin master

echo "All commits have been created and pushed!"
