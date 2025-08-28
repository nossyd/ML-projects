import torch.multiprocessing as mp
from torch.utils.data.distributed import DistributedSampler
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.distributed import init_process_group, destroy_process_group
from torch.utils.data import DataLoader
import torch.nn.functional as F
import torch
import os

class NeuralNetwork(torch.nn.Module):
    # parameterize num of inputs & outputs to reuse same code for diff datasets with diff num of features and classes
    def __init__(self, num_inputs, num_outputs):
        super().__init__()

        self.layers = torch.nn.Sequential(

            # first hidden layer
            # Linear layer takes num of input and output nodes as args
            torch.nn.Linear(num_inputs, 30),
            # Nonlinear activation functions are placed bw hidden layers
            torch.nn.ReLU(),

            # second hidden layer
            # The num of output nodes in prev hidden layer is equal to input of next hidden layer
            torch.nn.Linear(30, 20),
            torch.nn.ReLU(),

            # output layer
            torch.nn.Linear(20, num_outputs),
        )
    
    def forward(self, x):
        logits = self.layers(x)
        # the output of the last layer are called logits
        return logits
    

# prediction accuracy function
def compute_accuracy(model, dataloader):
    """Function to compute prediction accuracy of pytorch model

    Args:
        model (_type_): Neural Network pytorch class
        dataloader (_type_): Dataloader pytorch class
    """

    model = model.eval()
    correct = 0.0
    total_examples = 0

    for idx, (features, labels) in enumerate(dataloader):
        with torch.no_grad():
            logits = model(features)

        predictions = torch.argmax(logits, dim=1)
        compare = labels == predictions
        correct += torch.sum(compare)
        total_examples += len(compare)

    return (correct / total_examples).item()
    

def ddp_setup(rank, world_size):
    # address of the mauin node
    os.environ["MASTER_ADDR"] = "localhost"
    # any free port on machine
    os.environ["MASTER_PORT"] = "12345"
    
    init_process_group(
        backend="nccl",
        rank=rank,
        world_size=world_size
    )
    torch.cuda.set_device(rank)

def prepare_dataset(train_ds, test_ds):
    # insert dataset prep code
    train_loader = DataLoader(
        dataset=train_ds,
        batch_size=2,
        shuffle=False,
        pin_memory=True,
        drop_last=True,
        sampler=DistributedSampler(train_ds)
    )

    test_loader = DataLoader(
        dataset=test_ds,
        batch_size=2,
        shuffle=False,
        pin_memory=True,
        drop_last=True,
        sampler=DistributedSampler(test_ds)
    )
    return train_loader, test_loader

def main(rank, world_size, num_epochs):
    ddp_setup(rank, world_size)
    train_loader, test_loader = prepare_dataset()
    model = NeuralNetwork(num_inputs=2, num_outputs=2)
    model.to(rank)
    logits = model(features)
    loss = F.cross_entropy(logits, labels)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.5)
    loss.backward()
    optimizer.step()
    model = DDP(model, device_ids=[rank])
    for epoch in range(num_epochs):
        for features, labels in train_loader:
            features, labels = features.to(rank), labels.to(rank)
            # insert model prediction and backprop code
            print(f"[GPU{rank}] Epoch: {epoch+1:03d}/{num_epochs:03d}"
                  f" | Batchsize {labels.shape[0]:03d}"
                  f" | Train/Val Loss: {loss:.2f}")
    model.eval()
    train_acc = compute_accuracy(model, train_loader, device=rank)
    print(f"[GPU{rank}] Training Accuracy = ", train_acc)
    test_acc = compute_accuracy(model, test_loader, device=rank)
    print(f"[GPU{rank}] Test Accuracy = ", test_acc)
    destroy_process_group()

if __name__ == "__main__":
    print("Number of GPUs available: ", torch.cuda.device_count())
    torch.manual_seed(123)
    num_epochs = 3
    world_size = torch.cuda.device_count()
    mp.spawn(main, args=(world_size, num_epochs), nprocs=world_size)
