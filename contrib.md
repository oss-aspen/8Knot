## Submitting a Contribution
If you are interested in making a code contribution and would like to learn more about the technologies that we use, check out the list below.

1. Find an issue that you are interested in addressing or a feature that you would like to add.
2. Fork the repository associated with the issue to your local GitHub organization. This means that you will have a copy of the repository under your-GitHub-username/repository-name.
3. Clone the repository to your local machine using git clone [https://github.com/sandiego-rh/explorer.git](https://github.com/sandiego-rh/explorer.git).
4. Create a new branch for your fix using git checkout -b branch-name-here.
5. Make the appropriate changes for the issue you are trying to address or the feature that you want to add.
6. Use git add insert-paths-of-changed-files-here to add the file contents of the changed files to the "snapshot" git uses to manage the state of the project, also known as the index.
7. Use git commit -m "Insert a short message of the changes made here" to store the contents of the index with a descriptive message.
8. Push the changes to the remote repository using git push origin branch-name-here.
9. Submit a pull request to the upstream repository.
10. Title the pull request with a short description of the changes made and the issue or bug number associated with your change. For example, you can title an issue like so "Added more log outputting to resolve #4352".
11. In the description of the pull request, explain the changes that you made, any issues you think exist with the pull request you made, and any questions you have for the maintainer. It's OK if your pull request is not perfect (no pull request is), the reviewer will be able to help you fix any problems and improve it!
12. Wait for the pull request to be reviewed by a maintainer.
13. Make changes to the pull request if the reviewing maintainer recommends them.
14. Celebrate your success after your pull request is merged!

## Steps to create a new visulization
1. Make a new file for the visualization and put it in the folder of the [page](https://github.com/sandiego-rh/explorer/tree/main/pages) you want to add it to
2. Once the file is created, import the card to the respective page file and put it into the layout
IF you need to add a new query:
3. add a ddc.store componet to the (app.py)[https://github.com/sandiego-rh/explorer/blob/main/app.py]
4. Create the call back in the (app_callback.py)[https://github.com/sandiego-rh/explorer/blob/main/app_callbacks.py]for the data query in a similar format to the 3 at the bottom

## Steps to create a new page
1. Add a file to the (pages)[https://github.com/sandiego-rh/explorer/tree/dev/pages] folder with the same format as the others
2. Create a new folder in the (visualizations)[https://github.com/sandiego-rh/explorer/tree/main/pages/visualizations] for the respective page name

## Where can I go for help?
If you need help, you can ask questions on our Slack instance at [sandiego-rkb3936.slack.com](https://sandiego-rkb3936.slack.com).
