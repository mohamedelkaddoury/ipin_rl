import SOURCE.drl_agent as AG
import SOURCE.Environment as ENV
import numpy as np
import math

# ----------------------------------
# IndoorLoc_DRL class
# Get the location of a set of samples using a DRL-based algorithm
# ----------------------------------
class IndoorLocDRL:
    # ---------------------------------------------------------
    # Class constructor
    # train_fingerprints is a np array of n_train_samples x n_aps.
    #    Each element i,j is the RSSI in the i-th location from the j-th AP
    # train_locations is a np array of train_samples x 2.
    #    Each element i is the coordinates x,y of i-th train fingerprint
    # ---------------------------------------------------------
    def __init__(self, train_fingerprints, train_locations, conf, do_training=True, do_grid_mode= True, training_filename="drl.model"):
        self.train_fingerprints = train_fingerprints
        self.train_locations = train_locations
        self.n_training_samples = train_fingerprints.shape[0]
        self.n_aps = train_fingerprints.shape[1]
        self.N_EPISODES_PER_FP = conf.ENV_N_EPISODES_PER_FP

        # create environment and agent
        self.env = ENV.envivonment(self.n_aps, self.train_locations, conf)
        self.agent = AG.drl_agent(self.env, conf)
        self.training_filename = training_filename
        self.grid_mode = do_grid_mode
        self.AGENT_N_EPOCHS = conf.AGENT_N_EPOCHS

        if do_training:
            self.train()
            self.agent.save_to_disk(self.training_filename)
        else:
            self.agent.load_from_disk(self.training_filename)

    # ---------------------------------------------------------
    # ---------------------------------------------------------
    def train(self):
        if self.grid_mode:
            episodes, episodes_real_loc = self.env.generate_episodes_grid(self.train_fingerprints, self.train_locations)
        else:
            episodes, episodes_real_loc = self.env.generate_episodes_random(self.train_fingerprints, self.train_locations)
        self.agent.train(episodes, episodes_real_loc)

    # ---------------------------------------------------------
    # estimate_accuracy
    # ---------------------------------------------------------
    # Estimate the location accuracy of the estimated locations given the true ones.
    # ---------------------------------------------------------
    def estimate_accuracy(self, estimated_locations, true_locations):
        n_samples = estimated_locations.shape[0]
        v_errors = np.zeros(n_samples)
        for i in range(n_samples):
            v_errors[i] = self.env.get_distance(estimated_locations[i, :], true_locations[i, :])

        return v_errors

    # ---------------------------------------------------------
    # get_accuracy
    # ---------------------------------------------------------
    # Get statistics of the accuracy of a set of test fingerprints
    # ---------------------------------------------------------
    def get_accuracy(self, test_fingerprints, test_locations):

        estimated_locations = self.get_locations(test_fingerprints)
        v_errors = self.estimate_accuracy(estimated_locations, test_locations)

        return estimated_locations, v_errors, np.mean(v_errors), np.percentile(v_errors, 75)

    # ---------------------------------------------------------
    # get_location
    # ---------------------------------------------------------
    # Given a test fingerprint, return the estimated location (x,y) for this fingerprint
    # All the samples are in the same floor
    # ---------------------------------------------------------
    def get_location(self, fp):
        observation, n_steps = self.agent.test(fp)
        return observation[self.n_aps:self.n_aps+2]

    # ---------------------------------------------------------
    # get_locations
    # ---------------------------------------------------------
    # Get the location of a set of test_fingerprints
    # ---------------------------------------------------------
    def get_locations(self, test_fingerprints):
        n_test = test_fingerprints.shape[0]
        est_locations = np.zeros((n_test, 2))

        i = 0
        for fp in test_fingerprints:
            est_locations[i, ] = self.get_location(fp)
            i += 1

        return est_locations
