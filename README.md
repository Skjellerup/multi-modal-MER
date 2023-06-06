# multi-modal-MER
The purpose of this research paper is to explore the effect of auditory and language-based modalities on emotional responses, in the context of music. We aim to show that feeding these modalities to different regression models can yield varying results on the emotion a song is expected to evoke. To achieve this goal, we constructed a dataset of auditory features, gathered from the Spotify API, combined with language features such as sentiment scores and TF-IDF. This let us predict the valence and arousal score (VA score) which are metrics used to determine the evoked emotion (Russell 1980). With the use of various regression models, including random forest regressor, support vector regressor, and a neural network, we study how the predictions are affected by the two modalities.

The outcome of our study finds that random forest and support vector regressors performed for mood prediction in music, while the neural network is unfit for the task, considering our dataset. Additionally, we have found that using multimodal features to train our models generally performs better than uniform features.

### Requirements
All code was produced and tested using Python 3.10.6, with the dependencies described in [requirements_models.txt](requirements_models.txt) and [requirements_utilities.txt](requirements_utilities.txt)
